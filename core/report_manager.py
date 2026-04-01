import os
import subprocess
import platform
import datetime

from core.pdf_templates import PDFGenerator


class ReportGenerator:
    def __init__(self, db_manager, file_manager):
        self.db = db_manager
        self.fm = file_manager
        self.pdf_gen = PDFGenerator()
        self.pdf_gen.set_company_data(
            name=self.db.get_setting('company_name') or "Minta Kft.",
            address=self.db.get_setting('company_address') or "1234 Budapest, Minta u. 1.",
            tax=self.db.get_setting('company_tax') or "12345678-1-12",
            email=self.db.get_setting('company_email') or "info@minta.hu",
            phone1=self.db.get_setting('company_phone') or "+36 30 123 4567",
            phone2=self.db.get_setting('company_phone2') or "",
            phone3=self.db.get_setting('company_phone3') or "",
            bank_huf=self.db.get_setting('company_bank') or "00000000-00000000",
            bank_eur=self.db.get_setting('company_bank_eur') or "",
            reg_num=self.db.get_setting('company_reg') or "00000000",
            worker_name=self.db.get_setting('worker_name') or "Minta Dolgozó"
        )

    def open_pdf(self, filepath):
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            print(f"Hiba a PDF megnyitásakor: {e}")

    # ==========================================
    # PÉNZÜGYI MOTOR (FINANCIAL ENGINE)
    # ==========================================
    def _calculate_log_financials(self, log, contract):
        base_fee = float(contract.get('fee_amount', 0))
        fee_type = contract.get('fee_type', 'Óradíj')

        m_over = float(contract.get('mult_overtime', 50)) / 100.0
        m_week = float(contract.get('mult_weekend', 50)) / 100.0
        m_holi = float(contract.get('mult_holiday', 100)) / 100.0
        m_night = float(contract.get('mult_night', 25)) / 100.0
        ot_limit = float(contract.get('mult_overtime_threshold', 8.0))

        tr_bp = float(contract.get('travel_bp', 7000))
        tr_km = float(contract.get('travel_km', 250))

        events = log.get('events', [])
        night_work_hours = 0.0
        total_tr_dist = 0.0
        total_tr_time = 0.0

        has_office_travel = False
        has_private_travel = False
        first_t_start, last_t_end = "", ""
        time_summary = []

        for ev in events:
            diff = 0.0
            try:
                s = datetime.datetime.strptime(ev['start'], "%H:%M")
                e = datetime.datetime.strptime(ev['end'], "%H:%M")
                diff = (e - s).total_seconds() / 3600.0
                if diff < 0: diff += 24.0
            except:
                pass

            night_flag = ""
            if ev.get('is_night', 0):
                night_work_hours += diff
                night_flag = "[Éjszakai] "

            if ev['type'] == 'work':
                time_summary.append([ev['start'], ev['end'], f"{night_flag}{ev['desc']}"])
            elif ev['type'] == 'travel':
                total_tr_dist += float(ev.get('t_dist', 0))
                total_tr_time += diff
                t_type = ev.get('t_type', '')
                if not first_t_start: first_t_start = ev.get('t_start', '')
                last_t_end = ev.get('t_end', '')
                if t_type == 'Iroda':
                    has_office_travel = True
                elif t_type == 'Magán autó Céges használat':
                    has_private_travel = True
                desc = f"Utazás: {ev.get('t_start', '')} -> {ev.get('t_end', '')} ({ev.get('t_dist', 0)}km)"
                time_summary.append([ev['start'], ev['end'], desc])

        w_hours = float(log.get('engineer_hours', 0.0))
        is_holiday = log.get('is_holiday', 0)
        is_saturday = False
        try:
            d_obj = datetime.datetime.strptime(log['date'], "%Y.%m.%d.")
            if d_obj.weekday() == 5: is_saturday = True
        except:
            pass

        normal_hours = min(w_hours, ot_limit)
        overtime_hours = max(0, w_hours - ot_limit)

        base_fee_total = 0.0
        overtime_fee_total = 0.0
        night_fee_total = 0.0
        weekend_fee_total = 0.0
        holiday_fee_total = 0.0

        if fee_type == 'Óradíj':
            base_fee_total = w_hours * base_fee
            overtime_fee_total = overtime_hours * base_fee * m_over
            night_fee_total = night_work_hours * base_fee * m_night
            if is_holiday:
                holiday_fee_total = w_hours * base_fee * m_holi
            elif is_saturday:
                weekend_fee_total = w_hours * base_fee * m_week
            work_fee = base_fee_total + overtime_fee_total + night_fee_total + holiday_fee_total + weekend_fee_total
        elif fee_type == 'Napidíj':
            base_fee_total = base_fee
            if is_holiday:
                holiday_fee_total = base_fee * m_holi
            elif is_saturday:
                weekend_fee_total = base_fee * m_week
            work_fee = base_fee_total + holiday_fee_total + weekend_fee_total
        else:
            base_fee_total = base_fee
            work_fee = base_fee_total

        travel_fee = 0.0
        travel_calc_str = "Nincs elszámolható utazási díj"
        travel_type_str = "Nincs utazás (HO)"

        if has_office_travel:
            travel_fee += tr_bp
            travel_calc_str = f"Kiszállás (Budapest fix): {int(tr_bp):,} Ft"
            travel_type_str = "Iroda"
        elif has_private_travel:
            travel_fee += total_tr_dist * tr_km
            travel_calc_str = f"{total_tr_dist:g} km * {int(tr_km):,} Ft/km = {int(travel_fee):,} Ft"
            travel_type_str = "Magán autó Céges használat"

        mat_cost = float(log.get('material_cost', 0.0))
        total_cost = work_fee + travel_fee + mat_cost

        return {
            'work_fee': work_fee, 'travel_fee': travel_fee, 'mat_cost': mat_cost,
            'total_cost': total_cost, 'time_summary': time_summary,
            'travel_calc_str': travel_calc_str, 'travel_type_str': travel_type_str,
            'total_tr_dist': total_tr_dist, 'total_tr_time': total_tr_time,
            'first_t_start': first_t_start, 'last_t_end': last_t_end,
            'base_fee_total': base_fee_total, 'overtime_fee_total': overtime_fee_total,
            'night_fee_total': night_fee_total, 'weekend_fee_total': weekend_fee_total,
            'holiday_fee_total': holiday_fee_total, 'w_hours': w_hours,
            'overtime_hours': overtime_hours, 'night_hours': night_work_hours,
            'weekend_hours': w_hours if is_saturday else 0.0,
            'holiday_hours': w_hours if is_holiday else 0.0
        }

    # ==========================================
    # PDF GENERÁLÓ METÓDUSOK
    # ==========================================
    def generate_report(self, project_code, logs, p_data):
        filename = f"Munkalap_{project_code}.pdf"
        self.pdf_gen.output_dir = self.fm.get_export_dir(project_code, 'Munkalap')
        contract = self.db.get_contract_data(p_data['contract_code'])
        if not contract: return False, "Szerződés nem található a kalkulációhoz!"

        total_work_time = 0.0
        total_tr_time = 0.0
        total_project_cost = 0.0
        w_rows = []

        for l in logs:
            fin = self._calculate_log_financials(l, contract)
            total_work_time += l['engineer_hours']
            total_tr_time += fin['total_tr_time']
            total_project_cost += fin['total_cost']

            w_rows.append([
                l['date'], l['activity'], l['result'],
                f"{l['engineer_hours']:g}", f"{fin['total_tr_time']:g}",
                f"{int(fin['total_cost']):,} Ft", l['attachment_id']
            ])

        w_data = {
            'iW_num': project_code, 'sOrder_link': p_data.get('client_ref', ''),
            'iContract_num': p_data.get('contract_code', ''), 'dStart_date': p_data.get('start_date', ''),
            'dClose_date': p_data.get('completion_date', '') or '-', 'iOW_time': f"{total_work_time:g}",
            'iOT_time': f"{total_tr_time:g}", 'iOO_Fee': f"{int(total_project_cost):,} Ft"
        }
        return True, self.pdf_gen.create_work(filename, w_data, w_rows)

    def generate_daily_report(self, log_id):
        log = self.db.get_log_details(log_id)
        if not log: return False, "Bejegyzés nem található."

        p_data = self.db.get_project_data(log['project_code'])
        contract = self.db.get_contract_data(p_data['contract_code'])
        end_client = self.db.get_client(p_data['end_client_name'])

        self.pdf_gen.output_dir = self.fm.get_export_dir(log['project_code'], 'JegyzoKonyv')

        protocol_id = log.get('attachment_id', '')
        if not protocol_id: protocol_id = f"J_{log_id}"

        fin = self._calculate_log_financials(log, contract)

        address = 'Távoli munkavégzés / HO'
        if fin['travel_type_str'] != 'Nincs utazás (HO)':
            address = end_client.get('address', 'Ismeretlen helyszín') if end_client else 'Ismeretlen'

        data = {
            'iW_num': protocol_id, 'sW_type': log['activity'], 'aW_address': address,
            'sOrder_link': p_data.get('client_ref', ''), 'dDate': log['date'],
            'ssTime_summary': fin['time_summary'], 'iTravel_fee': f"{int(fin['travel_fee']):,} Ft",
            'sLicense_plate': "-", 'sNat_of_usage': fin['travel_type_str'],
            'iDepart_dist': fin['total_tr_dist'],
            'sDepart_towns': fin['first_t_start'] if fin['first_t_start'] else 'Összesített',
            'iArriv_dist': 0, 'sArriv_towns': fin['last_t_end'] if fin['last_t_end'] else 'útvonal',
            'sCalc_of_fee': fin['travel_calc_str'], 'iW_fee': f"{int(fin['work_fee']):,}",
            'iW_time': f"{log['engineer_hours']:g}", 'iT_time': f"{fin['total_tr_time']:g}",
            'iO_fee': f"{int(fin['total_cost']):,} Ft",
            'iO_time': f"{log['engineer_hours'] + fin['total_tr_time']:g} óra",
            'ssW_desc': log['result'] if log['result'] else log['activity']
        }
        filename = f"JegyzoKonyv_{protocol_id.replace('/', '_')}.pdf"
        return True, self.pdf_gen.create_merge(filename, data)

    def generate_full_project_report(self, project_code):
        p_data = self.db.get_project_data(project_code)
        logs = self.db.get_daily_logs(project_code)
        contract = self.db.get_contract_data(p_data['contract_code'])
        end_client = self.db.get_client(p_data['end_client_name'])

        self.pdf_gen.output_dir = self.fm.get_project_base_dir(project_code)

        total_work_time, total_tr_time, total_project_cost = 0.0, 0.0, 0.0
        w_rows, logs_data = [], []

        for i, l in enumerate(sorted(logs, key=lambda x: x['log_id'])):
            l_detailed = self.db.get_log_details(l['log_id'])
            fin = self._calculate_log_financials(l_detailed, contract)

            total_work_time += l['engineer_hours']
            total_tr_time += fin['total_tr_time']
            total_project_cost += fin['total_cost']

            protocol_id = l['attachment_id'] or f"J{project_code.replace('WJP', '')}/{i + 1}"
            w_rows.append([
                l['date'], l['activity'], l['result'], f"{l['engineer_hours']:g}",
                f"{fin['total_tr_time']:g}", f"{int(fin['total_cost']):,} Ft", protocol_id
            ])

            address = 'Távoli munkavégzés / HO'
            if fin['travel_type_str'] != 'Nincs utazás (HO)':
                address = end_client.get('address', 'Ismeretlen') if end_client else 'Ismeretlen'

            logs_data.append({
                'iW_num': protocol_id, 'sW_type': l['activity'], 'aW_address': address,
                'sOrder_link': p_data.get('client_ref', ''), 'dDate': l['date'],
                'ssTime_summary': fin['time_summary'], 'iTravel_fee': f"{int(fin['travel_fee']):,} Ft",
                'sLicense_plate': "-", 'sNat_of_usage': fin['travel_type_str'],
                'iDepart_dist': fin['total_tr_dist'],
                'sDepart_towns': fin['first_t_start'] if fin['first_t_start'] else 'Összesített',
                'iArriv_dist': 0, 'sArriv_towns': fin['last_t_end'] if fin['last_t_end'] else 'útvonal',
                'sCalc_of_fee': fin['travel_calc_str'], 'iW_fee': f"{int(fin['work_fee']):,}",
                'iW_time': f"{l['engineer_hours']:g}", 'iT_time': f"{fin['total_tr_time']:g}",
                'iO_fee': f"{int(fin['total_cost']):,} Ft",
                'iO_time': f"{l['engineer_hours'] + fin['total_tr_time']:g} óra",
                'ssW_desc': l['result'] if l['result'] else l['activity']
            })

        w_data = {
            'iW_num': project_code, 'sOrder_link': p_data.get('client_ref', ''),
            'iContract_num': p_data.get('contract_code', ''), 'dStart_date': p_data.get('start_date', ''),
            'dClose_date': p_data.get('completion_date', '') or '-', 'iOW_time': f"{total_work_time:g}",
            'iOT_time': f"{total_tr_time:g}", 'iOO_Fee': f"{int(total_project_cost):,} Ft"
        }
        return True, self.pdf_gen.create_full_report(f"Teljes_Projekt_{project_code}.pdf", w_data, w_rows, logs_data)

    def generate_contract_settlement(self, contract_code, start_date, end_date):
        c_data = self.db.get_contract_data(contract_code)
        if not c_data: return False, "Szerződés nem található."

        self.db.c.execute("SELECT project_code, client_ref FROM projects WHERE contract_code=?", (contract_code,))
        projects_info = {r[0]: r[1] for r in self.db.c.fetchall()}
        proj_codes = list(projects_info.keys())
        if not proj_codes: return False, "Ehhez a szerződéshez még nem tartozik projekt."

        placeholders = ','.join('?' * len(proj_codes))
        query_params = proj_codes + [start_date, end_date]

        self.db.c.execute(f'''
            SELECT log_id, project_code, date, activity, engineer_hours, attachment_id, material_cost
            FROM daily_logs 
            WHERE project_code IN ({placeholders}) AND date >= ? AND date <= ?
            ORDER BY date ASC
        ''', tuple(query_params))

        columns = [desc[0] for desc in self.db.c.description]
        logs_raw = [dict(zip(columns, row)) for row in self.db.c.fetchall()]

        if not logs_raw: return False, f"Nincs elvégzett tevékenység ebben az időszakban."

        fw_rows = []
        total_work_time, total_travel_time, total_extra_cost, grand_total_fee = 0.0, 0.0, 0.0, 0.0

        ti_data = {
            'base_fee_total': 0.0, 'overtime_fee_total': 0.0, 'night_fee_total': 0.0,
            'weekend_fee_total': 0.0, 'holiday_fee_total': 0.0, 'travel_fee_total': 0.0,
            'mat_cost_total': 0.0, 'w_hours': 0.0, 'overtime_hours': 0.0,
            'night_hours': 0.0, 'weekend_hours': 0.0, 'holiday_hours': 0.0, 'total_cost': 0.0
        }

        ot_limit = float(c_data.get('mult_overtime_threshold', 8.0))

        for l in logs_raw:
            detailed_log = self.db.get_log_details(l['log_id'])
            fin = self._calculate_log_financials(detailed_log, c_data)

            total_work_time += l['engineer_hours']
            total_travel_time += fin['total_tr_time']

            extra_cost = fin['travel_fee'] + fin['mat_cost']
            total_extra_cost += extra_cost
            grand_total_fee += fin['total_cost']

            ti_data['base_fee_total'] += fin['base_fee_total']
            ti_data['overtime_fee_total'] += fin['overtime_fee_total']
            ti_data['night_fee_total'] += fin['night_fee_total']
            ti_data['weekend_fee_total'] += fin['weekend_fee_total']
            ti_data['holiday_fee_total'] += fin['holiday_fee_total']
            ti_data['travel_fee_total'] += fin['travel_fee']
            ti_data['mat_cost_total'] += fin['mat_cost']
            ti_data['w_hours'] += fin['w_hours']
            ti_data['overtime_hours'] += fin['overtime_hours']
            ti_data['night_hours'] += fin['night_hours']
            ti_data['weekend_hours'] += fin['weekend_hours']
            ti_data['holiday_hours'] += fin['holiday_hours']
            ti_data['total_cost'] += fin['total_cost']

            tulora_str = "Igen" if l['engineer_hours'] > ot_limit else "Nem"
            munkalap_str = l['project_code'].replace('WJP', 'M')
            melleklet_str = l['attachment_id'] or f"J{l['project_code'].replace('WJP', '')}/{l['log_id']}"
            cost_text = f"{int(extra_cost):,} Ft".replace(',', ' ') if extra_cost > 0 else "0 Ft"

            fw_rows.append([
                l['date'], munkalap_str, projects_info[l['project_code']],
                f"{l['engineer_hours']:g} óra", f"{fin['total_tr_time']:g} óra",
                cost_text, melleklet_str, tulora_str
            ])

        c_data['client'] = c_data['client_name']

        client_details = self.db.get_client(c_data['client_name'])
        if client_details:
            c_data['client_address'] = client_details.get('address', '')
            c_data['client_tax'] = client_details.get('tax_number', '')

        c_data['sEOJ_num'] = f"EOJ_{start_date.replace('.', '')[:6]}"
        c_data['sTI_num'] = f"T{start_date.replace('.', '')[:6]}"
        c_data['dStart'] = start_date
        c_data['dEnd'] = end_date
        c_data['iTotal_fee'] = f"{int(grand_total_fee):,} Ft".replace(',', ' ')
        c_data['iW_time_sum'] = f"{total_work_time:g} óra"
        c_data['iT_time_sum'] = f"{total_travel_time:g} óra"
        c_data['iCost_sum'] = f"{int(total_extra_cost):,} Ft".replace(',', ' ')

        target_dir = os.path.join(self.fm.base_dir, f"{contract_code}_{self.fm._sanitize(c_data['client_name'])}",
                                  "98_Elszamolas_osszesitok")
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        self.pdf_gen.output_dir = target_dir

        safe_start = start_date.replace('.', '')
        eoj_filename = f"Elszamolasi_Jegyzkonyv_{contract_code}_{safe_start}.pdf"
        ti_filename = f"Teljesites_Igazolas_{contract_code}_{safe_start}.pdf"

        eoj_path = self.pdf_gen.create_contract_report(eoj_filename, c_data, fw_rows)
        ti_path = self.pdf_gen.create_completion_certificate(ti_filename, c_data, ti_data)

        # Visszaadjuk mindkét fájl útvonalát!
        return True, eoj_path, ti_path

    def generate_document(self, doc_id):
        doc_data = self.db.get_document_content(doc_id)
        if not doc_data: return False, "Dokumentum nem található."
        p_data = self.db.get_project_data(doc_data['project_code'])
        if not p_data: return False, "A dokumentumhoz tartozó projekt nem található."

        target_dir = os.path.join(self.fm.get_project_base_dir(doc_data['project_code']), f"{doc_id}_mellekletek")
        if not os.path.exists(target_dir): os.makedirs(target_dir)

        self.pdf_gen.output_dir = target_dir
        filename = f"Dokumentum_{doc_id}_{self.fm._sanitize(doc_data['title'])}.pdf"
        return True, self.pdf_gen.create_document(filename, doc_data, p_data)