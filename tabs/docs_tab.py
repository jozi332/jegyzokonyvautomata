import os
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as sd

# Helyi importok a core mappából
from core.ui_components import safe_toplevel
from core.style_manager import NativeRichTextEditor


class DocsTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.db = self.app.db
        self.fm = self.app.fm
        self.rg = self.app.rg
        self._build_ui()

    def _build_ui(self):
        top_f = ttk.Frame(self, padding=10)
        top_f.pack(fill="x")
        ttk.Label(top_f, text="Projekt kiválasztása:").pack(side="left", padx=5)
        self.cb_doc_project = ttk.Combobox(top_f, state="readonly", width=30)
        self.cb_doc_project.pack(side="left", padx=5)
        self.cb_doc_project.bind("<<ComboboxSelected>>", lambda e: self.refresh_doc_list())

        btn_f = ttk.Frame(top_f)
        btn_f.pack(side="right")
        ttk.Button(btn_f, text="Új Dokumentum", command=lambda: self.open_doc_editor()).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Módosítás", command=self._edit_selected_doc).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Törlés", command=self._delete_selected_doc).pack(side="left", padx=5)
        ttk.Button(btn_f, text="PDF Generálás", command=self._generate_doc_pdf).pack(side="left", padx=5)

        list_f = ttk.LabelFrame(self, text="Projekt Dokumentumai", padding=10)
        list_f.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_docs = ttk.Treeview(list_f, columns=("ID", "Cím", "Dátum"), show='headings')
        self.tree_docs.heading("ID", text="Doc ID")
        self.tree_docs.heading("Cím", text="Cím")
        self.tree_docs.heading("Dátum", text="Létrehozva")
        self.tree_docs.pack(fill="both", expand=True)
        self.tree_docs.bind("<Double-1>", lambda e: self._edit_selected_doc())

        self.refresh_doc_project_list()

    def refresh_doc_project_list(self):
        projs = [r[0] for r in self.db.get_project_stats()]
        self.cb_doc_project['values'] = projs
        if projs and not self.cb_doc_project.get():
            self.cb_doc_project.current(0)
            self.refresh_doc_list()

    def refresh_doc_list(self):
        for i in self.tree_docs.get_children():
            self.tree_docs.delete(i)
        p_code = self.cb_doc_project.get()
        if p_code:
            for d in self.db.get_documents(p_code):
                self.tree_docs.insert("", "end", values=d)

    def _edit_selected_doc(self):
        sel = self.tree_docs.selection()
        if sel:
            self.open_doc_editor(self.tree_docs.item(sel[0], "values")[0])

    def _delete_selected_doc(self):
        sel = self.tree_docs.selection()
        if sel:
            doc_id = self.tree_docs.item(sel[0], "values")[0]
            if messagebox.askyesno("Törlés", f"Biztosan törlöd a dokumentumot: {doc_id}?"):
                self.db.delete_document(doc_id)
                self.refresh_doc_list()

    def open_doc_editor(self, doc_id=None):
        p_code = self.cb_doc_project.get()
        if not p_code:
            messagebox.showwarning("Hiba", "Előbb válassz ki egy projektet!")
            return

        is_new = doc_id is None
        if is_new:
            count = len(self.db.get_documents(p_code)) + 1
            doc_id = f"D{p_code.replace('WJP', '').replace('S', '').replace('P', '')}/{count}"
            data = {'doc_id': doc_id, 'project_code': p_code, 'title': '', 'content': '',
                    'created_date': datetime.date.today().strftime("%Y.%m.%d.")}
        else:
            data = self.db.get_document_content(doc_id)

        top = safe_toplevel(self, f"Dokumentum Szerkesztő: {doc_id}", "900x700")

        top_f = ttk.Frame(top, padding=10)
        top_f.pack(fill="x")
        ttk.Label(top_f, text="Dokumentum Címe:").pack(side="left")
        ent_title = ttk.Entry(top_f, width=50)
        ent_title.insert(0, data['title'])
        ent_title.pack(side="left", padx=10)

        tool_f = ttk.Frame(top)
        tool_f.pack(fill="x", padx=10)

        def attach_file():
            filepath = filedialog.askopenfilename(title="Fájl kiválasztása csatoláshoz", parent=top)
            if filepath:
                orig_name = os.path.basename(filepath)
                new_name = sd.askstring("Fájl átnevezése", "Milyen néven mentsük le?", initialvalue=orig_name,
                                        parent=top)
                if new_name:
                    doc_dir = self.fm.get_export_dir(p_code, 'Dokumentum')
                    target_dir = os.path.join(doc_dir, f"{doc_id.replace('/', '_')}_mellekletek")
                    if not os.path.exists(target_dir): os.makedirs(target_dir)

                    target_path = os.path.join(target_dir, new_name)
                    try:
                        shutil.copy2(filepath, target_path)

                        # --- NEW: Image vs File Rendering Logic ---
                        if new_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                            txt_content.insert_image(target_path)
                        else:
                            txt_content.text_editor.insert("insert", f"\n[Csatolt Fájl: {new_name}]\n",
                                                           ("Normal", "align_center"))
                        # ------------------------------------------

                    except Exception as e:
                        messagebox.showerror("Hiba", f"Nem sikerült a fájl másolása:\n{e}", parent=top)

        ttk.Button(tool_f, text="Fájl/Kép Csatolás", command=attach_file).pack(side="right", padx=2)

        txt_content = NativeRichTextEditor(top, initial_content=data['content'])
        txt_content.pack(fill="both", expand=True, padx=10, pady=5)

        btn_f = ttk.Frame(top, padding=10)
        btn_f.pack(fill="x")

        def save():
            data['title'] = ent_title.get()
            data['content'] = txt_content.get_content()
            succ, msg = self.db.save_document(data)
            if succ:
                self.refresh_doc_list()
                top.destroy()
            else:
                messagebox.showerror("Hiba", msg, parent=top)

        ttk.Button(btn_f, text="Mentés", command=save).pack(side="right", padx=5)
        ttk.Button(btn_f, text="Mégse", command=top.destroy).pack(side="right", padx=5)

    def _generate_doc_pdf(self):
        sel = self.tree_docs.selection()
        if not sel: return
        doc_id = self.tree_docs.item(sel[0], "values")[0]
        data = self.db.get_document_content(doc_id)
        project = self.db.get_project_data(data['project_code'])

        filename = f"Dokumentum_{doc_id.replace('/', '_')}.pdf"
        try:
            target_dir = self.fm.get_export_dir(data['project_code'], 'Dokumentum')
            self.rg.pdf_gen.output_dir = target_dir
            full_path = self.rg.pdf_gen.create_document(filename, data, project)
            self.rg.open_pdf(full_path)
        except Exception as e:
            messagebox.showerror("Hiba a PDF generáláskor", str(e))