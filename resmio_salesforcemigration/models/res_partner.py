from odoo import api, fields, models, _, tools
import psycopg2
import uuid
from psycopg2.extras import execute_values
import datetime

import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _create_db_cursor(self):
        resmio_salesforcemigration_postgres_host = self.env['ir.config_parameter'].sudo().get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_host')
        resmio_salesforcemigration_postgres_database = self.env['ir.config_parameter'].sudo().get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_database')
        resmio_salesforcemigration_postgres_user = self.env['ir.config_parameter'].sudo().get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_user')
        resmio_salesforcemigration_postgres_password = self.env['ir.config_parameter'].sudo().get_param('resmio_salesforcemigration.resmio_salesforcemigration_postgres_password')
        try:
            conn = psycopg2.connect(
                host=resmio_salesforcemigration_postgres_host,
                database=resmio_salesforcemigration_postgres_database,
                user=resmio_salesforcemigration_postgres_user,
                password=resmio_salesforcemigration_postgres_password,
            )
        except psycopg2.Error:
            _logger.info('Connection to the database failed')
            raise

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        return cur

    def _get_facility_id_partner_mapping(self):
        partners_with_account_ids = self.env['res.partner'].search_read(
            [('facility_id', '!=', False)],
            ['id', 'facility_id'],
        )
        mapped_facility_ids = {}
        for p in partners_with_account_ids:
            mapped_facility_ids[p['facility_id']] = p['id']

        return mapped_facility_ids

    def _get_partners_with_salesforce_account_ids(self):
        partners_with_salesforce_account_ids = self.env['res.partner'].search_read(
            [('salesforce_account_id', '!=', False)],
            ['id', 'salesforce_account_id', 'name'],
        )
        mapped_salesforce_account_ids = {}
        for p in partners_with_salesforce_account_ids:
            mapped_salesforce_account_ids[p['salesforce_account_id']] = {
                'id': p['id'],
                'name': p['name'],
            }

        return mapped_salesforce_account_ids

    def _get_partners_with_salesforce_contact_ids(self):
        partners_with_salesforce_contact_ids = self.env['res.partner'].search_read(
            [('salesforce_contact_id', '!=', False)],
            ['id', 'salesforce_contact_id', 'name'],
        )
        mapped_salesforce_contact_ids = {}
        for p in partners_with_salesforce_contact_ids:
            mapped_salesforce_contact_ids[p['salesforce_contact_id']] = {
                'id': p['id'],
                'name': p['name'],
            }

        return mapped_salesforce_contact_ids

    def _get_leads_with_salesforce_lead_id(self):
        leads_with_salesforce_lead_ids = self.env['crm.lead'].search_read(
            [('salesforce_lead_id', '!=', False)],
            ['id', 'salesforce_lead_id'],
        )
        mapped_salesforce_lead_ids = {}
        for l in leads_with_salesforce_lead_ids:
            mapped_salesforce_lead_ids[l['salesforce_lead_id']] = l['id']

        return mapped_salesforce_lead_ids

    def _get_phone_calls_with_salesforce_task_id(self):
        leads_with_salesforce_task_ids = self.env['crm.phonecall'].search_read(
            [('salesforce_task_id', '!=', False)],
            ['id', 'salesforce_task_id'],
        )
        mapped_salesforce_task_ids = {}
        for l in leads_with_salesforce_task_ids:
            mapped_salesforce_task_ids[l['salesforce_task_id']] = l['id']

        return mapped_salesforce_task_ids

    def _get_helpdesk_tickets_with_salesforce_task_id(self):
        leads_with_salesforce_task_ids = self.env['helpdesk.ticket'].search_read(
            [('salesforce_task_id', '!=', False)],
            ['id', 'salesforce_task_id'],
        )
        mapped_salesforce_task_ids = {}
        for l in leads_with_salesforce_task_ids:
            mapped_salesforce_task_ids[l['salesforce_task_id']] = l['id']

        return mapped_salesforce_task_ids

    def _get_country_ids_by_code(self):
        partners_with_country_ids = self.env['res.country'].search_read(
            [],
            ['id', 'code'],
        )
        mapped_country_ids = {}
        for c in partners_with_country_ids:
            mapped_country_ids[c['code']] = c['id']

        return mapped_country_ids

    def _get_user_partner_ids_by_email(self):
        partners_with_partner_ids = self.env['res.users'].search_read(
            [],
            ['partner_id', 'login'],
        )
        mapped_partner_ids = {}
        for p in partners_with_partner_ids:
            mapped_partner_ids[p['login'].lower()] = p['partner_id'][0]

        # Maps denniver@resmio.com to denniver.schuch@resmio.com
        if 'denniver.schuch@resmio.com' in partners_with_partner_ids:
            mapped_partner_ids['denniver@resmio.com'] = partners_with_partner_ids['denniver.schuch@resmio.com']

        return mapped_partner_ids

    @api.model
    def _sync_companies_from_salesforce(self):
        mapped_country_ids = self._get_country_ids_by_code()
        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()

        mapped_facility_ids = self._get_facility_id_partner_mapping()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()

        cur.execute("""SELECT a.id, accountid__c, facility_id__c, active_mrr_c__c, backend_status__c, billingcity, billingcountry, billingpostalcode, billingstate, billingstreet, bitburger_kundennummer__c,
               LOWER(c.email) as createdby_email, a.createddate, customerstatusauto__c, dsgvo_gdor__c, email__c, facebookpage__c,  gesch_ftspartner__c,
               kaltakquise__c, language__c, masterrecordid, a.name, LOWER(o.email) as owner_email,    parentid, a.phone,recordtypeid, subscription_type__c,    vat_number__c, valid_payment_information__c, website,
               cmp_campaign__c,cmp_content__c, cmp_medium__c,  cmp_name__c, cmp_source__c,    cmp_term__c, mslatestcontractreasonfortermination__c, type__c, verified_admin__c
        FROM account a
        LEFT JOIN user2 c on a.createdbyid = c.id
        LEFT JOIN user2 o on a.ownerid = o.id""")

        accounts = cur.fetchall()

        # update
        # create

        updates = []
        inserts = []
        new_tags = []

        for acc in accounts:
            if acc['id'] in mapped_salesforce_account_ids:
                # TODO check which fields we want to take over
                # updates.append({
                #     'id': mapped_salesforce_account_ids[acc['id']],
                #     'salesforce_account_id': acc['id'],
                # })
                pass
            elif acc['facility_id__c'] and acc['facility_id__c'] in mapped_facility_ids:
                # TODO check which fields we want to take over (same as above)
                updates.append({
                    'id': mapped_facility_ids[acc['facility_id__c']],
                    'salesforce_account_id': acc['id'],
                    'businesspartner': acc['gesch_ftspartner__c'],
                    'create_uid': mapped_user_partner_ids[acc['createdby_email']] if acc['createdby_email'] in mapped_user_partner_ids else 1,
                    'user_id': mapped_user_partner_ids[acc['owner_email']] if acc['owner_email'] in mapped_user_partner_ids else None,
                })
            else:
                inserts.append({
                    'salesforce_account_id': acc['id'],
                    'name': acc['name'],
                    'lang': 'de_DE' if acc['language__c'] == 'de' else 'en_US',
                    'vat': acc['vat_number__c'],
                    'website': acc['website'],
                    'street': acc['billingstreet'],
                    'zip': acc['billingpostalcode'],
                    'city': acc['billingcity'],
                    'country_id': mapped_country_ids[acc['billingcountry'].upper()] if acc['billingcountry'] and acc['billingcountry'].upper() in mapped_country_ids else None,
                    'bitburger_customer_number': acc['bitburger_kundennummer__c'],
                    'email': acc['email__c'],
                    'email_normalized': tools.email_normalize(acc['email__c']) or acc['email__c'],
                    'phone': acc['phone'],
                    'create_date': acc['createddate'],
                    'facebookpage': acc['facebookpage__c'],
                    'businesspartner': acc['gesch_ftspartner__c'],
                    'create_uid': mapped_user_partner_ids[acc['createdby_email']] if acc['createdby_email'] in mapped_user_partner_ids else 1,
                    'cmp_campaign': acc['cmp_campaign__c'],
                    'cmp_content': acc['cmp_content__c'],
                    'cmp_medium': acc['cmp_medium__c'],
                    'cmp_name': acc['cmp_name__c'],
                    'cmp_source': acc['cmp_source__c'],
                    'cmp_term': acc['cmp_term__c'],
                    'user_id': mapped_user_partner_ids[acc['owner_email']] if acc['owner_email'] in mapped_user_partner_ids else None,

                    # TODO add mslatestcontractreasonfortermination__c
                })
                if acc['type__c'] == 'Partner':
                    new_tags.append(acc['id'])

        insert_query = """INSERT INTO res_partner (
            salesforce_account_id,
            name,
            display_name,
            lang,
            vat,
            website,
            active,
            type,
            street,
            zip,
            city,
            country_id,
            bitburger_customer_number,
            email,
            phone,
            create_date,
            facebookpage,
            businesspartner,
            create_uid,
            cmp_campaign,
            cmp_content,
            cmp_medium,
            cmp_name,
            cmp_source,
            cmp_term,
            is_company,
            color,
            partner_share,
            commercial_company_name,
            write_uid,
            write_date,
            email_normalized,
            message_bounce,
            invoice_warn,
            supplier_rank,
            customer_rank,
            calendar_last_notif_ack,
            sale_warn,
            user_id
        )
        VALUES %s"""

        vals = [(i['salesforce_account_id'], i['name'], i['name'], i['lang'], i['vat'], i['website'], True, 'contact', i['street'],
                 i['zip'], i['city'], i['country_id'], i['bitburger_customer_number'], i['email'], i['phone'],
                 i['create_date'], i['facebookpage'], i['businesspartner'], i['create_uid'], i['cmp_campaign'],
                 i['cmp_content'], i['cmp_medium'], i['cmp_name'], i['cmp_source'], i['cmp_term'], True, 0, True,
                 i['name'], 1, datetime.datetime.now(), i['email_normalized'], 0, 'no-message', 0, 0,
                 datetime.datetime.now(), 'no-message', i['user_id']) for i in inserts]

        execute_values(self.env.cr, insert_query, vals)

        self.env.cr.execute("""
            UPDATE res_partner
            SET commercial_partner_id = id
            WHERE commercial_partner_id IS NULL AND salesforce_account_id IS NOT NULL
        """)

        # Tags all partners with the proper categories
        # Creates the category if it does not exist
        if len(new_tags) > 1:
            partner_categories = self.env['res.partner.category'].search([('name', '=', 'Partner')])
            if len(partner_categories) < 1:
                partner_categories = [self.env['res.partner.category'].create({'name': 'Partner'})]

            new_tags_salesforce_account_id_strings = ",".join([f"'{t}'" for t in new_tags])
            self.env.cr.execute(f"""INSERT INTO res_partner_res_partner_category_rel (category_id, partner_id) SELECT {partner_categories[0].id}, id FROM res_partner WHERE salesforce_account_id IN ({new_tags_salesforce_account_id_strings})""")


    @api.model
    def _sync_contacts_from_salesforce(self):
        mapped_country_ids = self._get_country_ids_by_code()
        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()
        mapped_salesforce_contact_ids = self._get_partners_with_salesforce_contact_ids()

        cur.execute("""SELECT c.id, c.accountid, billing_country__c, city__c, c.language__c, c.email, c.mobilephone, c.phone, salutation, c.firstname, c.lastname, c.createddate,
           LOWER(owner.email) as owner_email, LOWER(createdby.email) as createdby_email
        FROM contact c
        LEFT JOIN user2 createdby on c.createdbyid = createdby.id
        LEFT JOIN user2 owner on c.ownerid = owner.id""")

        accounts = cur.fetchall()

        # update
        # create

        updates = []
        inserts = []

        for acc in accounts:
            if acc['id'] in mapped_salesforce_contact_ids:
                # TODO check which fields we want to take over
                # updates.append({
                #     'id': mapped_salesforce_account_ids[acc['id']],
                #     'salesforce_account_id': acc['id'],
                # })
                pass
            elif acc['accountid'] and acc['accountid'] not in mapped_salesforce_account_ids:
                # We have a contact that belongs to an account that we don't know
                pass
            else:
                name_components = []
                if acc['firstname']:
                    name_components.append(acc['firstname'])
                if acc['lastname']:
                    name_components.append(acc['lastname'])

                if len(name_components) > 0:
                    name = ' '.join(name_components)
                else:
                    name = acc['id']
                commercial_company_name = name
                display_name = name
                user_id = None

                parent_id = mapped_salesforce_account_ids[acc['accountid']]['id'] if acc['accountid'] and acc['accountid'] in mapped_salesforce_account_ids else None
                if acc['accountid'] and acc['accountid'] in mapped_salesforce_account_ids:
                    commercial_company_name = mapped_salesforce_account_ids[acc['accountid']]['name']
                    display_name = commercial_company_name + ', ' + name
                    user_id = mapped_user_partner_ids[acc['owner_email']] if acc['owner_email'] in mapped_user_partner_ids else None,

                inserts.append({
                    'salesforce_contact_id': acc['id'],
                    'commercial_partner_id': parent_id,
                    'parent_id': parent_id,
                    'is_company': parent_id is None,
                    'name': name,
                    'commercial_company_name': commercial_company_name,
                    'display_name': display_name,
                    'lang': 'de_DE' if acc['language__c'] == 'de' else 'en_US',
                    'city': acc['city__c'],
                    'country_id': mapped_country_ids[acc['billing_country__c'].upper()] if acc['billing_country__c'] and acc['billing_country__c'].upper() in mapped_country_ids else None,
                    'email': acc['email'],
                    'email_normalized': tools.email_normalize(acc['email']) or acc['email'],
                    'phone': acc['phone'],
                    'mobile': acc['mobilephone'],
                    'create_date': acc['createddate'],
                    'create_uid': mapped_user_partner_ids[acc['createdby_email']] if acc['createdby_email'] in mapped_user_partner_ids else 1,
                    'user_id': user_id,
                })

        insert_query = """INSERT INTO res_partner (
            salesforce_contact_id,
            name,
            display_name,
            commercial_partner_id,
            lang,
            vat,
            website,
            active,
            type,
            street,
            zip,
            city,
            country_id,
            bitburger_customer_number,
            email,
            phone,
            mobile,
            create_date,
            facebookpage,
            businesspartner,
            create_uid,
            cmp_campaign,
            cmp_content,
            cmp_medium,
            cmp_name,
            cmp_source,
            cmp_term,
            is_company,
            color,
            partner_share,
            commercial_company_name,
            write_uid,
            write_date,
            email_normalized,
            message_bounce,
            invoice_warn,
            supplier_rank,
            customer_rank,
            calendar_last_notif_ack,
            sale_warn,
            user_id
        )
        VALUES %s"""

        vals = [(i['salesforce_contact_id'], i['name'], i['name'], i['commercial_partner_id'], i['lang'], None, None, True, 'contact', None,
                 None, i['city'], i['country_id'], None, i['email'], i['phone'], i['mobile'],
                 i['create_date'], None, None, i['create_uid'], None,
                 None, None, None, None, None, i['is_company'], 0, True,
                 i['commercial_company_name'], 1, datetime.datetime.now(), i['email_normalized'], 0, 'no-message', 0, 0,
                 datetime.datetime.now(), 'no-message', user_id) for i in inserts]

        execute_values(self.env.cr, insert_query, vals)

        self.env.cr.execute("""
            UPDATE res_partner
            SET commercial_partner_id = id
            WHERE commercial_partner_id IS NULL AND salesforce_contact_id IS NOT NULL
        """)


    @api.model
    def _sync_leads_and_opportunities(self):

        mapped_country_ids = self._get_country_ids_by_code()
        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()
        mapped_salesforce_contact_ids = self._get_partners_with_salesforce_contact_ids()

        mapped_salesforce_lead_ids = self._get_leads_with_salesforce_lead_id()

        cur.execute("""SELECT l.id, convertedaccountid, regexp_replace(replace(anschrift__c, '</p><p>', '\n'), E'<[^>]+>', '', 'gi') as description,
               l.city, COALESCE(o.name, l.company) as name, company, convertedcontactid,
               converteddate, convertedopportunityid, l.country,
               country_code__c, COALESCE(LOWER(opportunity_owner.email), LOWER(lead_owner.email)) as owner_email,
                COALESCE(LOWER(lead_createdby.email), LOWER(opportunity_createdby.email)) as createdby_email,
               l.createddate, o.createddate as date_conversion, COALESCE(o.createddate, l.createddate) as date_open, dsgvo_gdpr__c, COALESCE(l.email, fb_email__c) as email_from,
               l.mobilephone as mobilephone, COALESCE(l.phone, l.fb_phone__c) as phone, facebookseite__c, l.firstname, l.lastname, isconverted, l.isdeleted, l.kaltakquise__c, language__c,
               COALESCE(o.lastactivitydate, l.lastactivitydate) as lastactivitydate, COALESCE(o.lastmodifiedbyid, l.lastmodifiedbyid) as lastmodifiedbyid,
               COALESCE(o.lastmodifieddate, l.lastmodifieddate) as lastmodifieddate, COALESCE(o.lastreferenceddate, l.lastreferenceddate) as lastreferenceddate,
               lasttransferdate, COALESCE(o.lastvieweddate, l.lastvieweddate) as lastvieweddate,
               lead_assign_number__c, openinghours__c, photourl,l.postalcode, l.street, COALESCE(o.systemmodstamp, l.systemmodstamp) as systemmodstamp, l.title, website,
               backend_subscription__c, cmp_campaign__c, cmp_content__c, cmp_medium__c, cmp_name__c, cmp_source__c, cmp_term__c, leadcap__facebook_lead_id__c,
               type__c, closedate, isclosed, iswon, amount, expectedrevenue,
               CASE
                   WHEN o.id is NULL THEN 'lead'
                   ELSE 'opportunity'
               END as type
        FROM lead l
        LEFT JOIN opportunity o on l.convertedopportunityid = o.id
        LEFT JOIN user2 lead_createdby on l.createdbyid = lead_createdby.id
        LEFT JOIN user2 lead_owner on l.ownerid = lead_owner.id
        LEFT JOIN user2 opportunity_createdby on o.createdbyid = opportunity_createdby.id
        LEFT JOIN user2 opportunity_owner on o.ownerid = opportunity_owner.id""")


        leads = cur.fetchall()

        # update
        # create

        updates = []
        inserts = []
        new_tags = []

        recurring_plan_ids = self.env['crm.recurring.plan'].search([('number_of_months', '=', 1)])
        if len(recurring_plan_ids) < 1:
            recurring_plan_ids = [self.env['crm.recurring.plan'].create({'number_of_months': 1, 'name': 'Monthly'})]

        for lead in leads:
            if lead['id'] in mapped_salesforce_lead_ids:
                # TODO check which fields we want to take over
                # updates.append({
                #     'id': mapped_salesforce_lead_ids[lead['id']],
                #     'salesforce_account_id': lead['id'],
                # })
                pass
            else:
                name_components = []
                if lead['firstname']:
                    name_components.append(lead['firstname'])
                if lead['lastname']:
                    name_components.append(lead['lastname'])

                contact_name = None
                if len(name_components) > 0:
                    contact_name = ' '.join(name_components)

                partner_id = None
                partner_name = None
                if lead['convertedaccountid'] in mapped_salesforce_account_ids:
                    partner_id = mapped_salesforce_account_ids[lead['convertedaccountid']]['id']
                    partner_name = mapped_salesforce_account_ids[lead['convertedaccountid']]['name']
                elif lead['convertedcontactid'] in mapped_salesforce_contact_ids:
                    partner_id = mapped_salesforce_account_ids[lead['convertedcontactid']]
                    partner_name = mapped_salesforce_account_ids[lead['convertedcontactid']]['name']

                probability = 0.1
                if lead['isclosed'] and lead['iswon']:
                    probability = 100
                elif lead['isclosed'] and not lead['iswon']:
                    probability = 0

                country_id = None
                if lead['country_code__c'] is not None and lead['country_code__c'].upper() in mapped_country_ids:
                    country_id = mapped_country_ids[lead['country_code__c'].upper()]
                elif lead['country'] is not None and lead['country'].upper() in mapped_country_ids:
                    country_id = mapped_country_ids[lead['country'].upper()]
                elif lead['country'] is not None and lead['country'].upper() in ['GERMANY', 'DEUTSCHLAND', 'ALEM??N'] and 'DE' in mapped_country_ids:
                    country_id = mapped_country_ids['DE']
                elif lead['country'] is not None and lead['country'].upper() in ['FRANCE', 'FRANKREICH'] and 'FR' in mapped_country_ids:
                    country_id = mapped_country_ids['FR']
                elif lead['country'] is not None and lead['country'].upper() in ['SCHWEIZ', 'SWITZERLAND'] and 'CH' in mapped_country_ids:
                    country_id = mapped_country_ids['CH']
                elif lead['country'] is not None and lead['country'].upper() in ['??STERREICH', 'AUSTRIA'] and 'AT' in mapped_country_ids:
                    country_id = mapped_country_ids['AT']

                recurring_revenue_monthly_prorated = None
                if lead['expectedrevenue'] is not None:
                    recurring_revenue_monthly_prorated = lead['expectedrevenue']
                elif lead['amount'] is not None:
                    recurring_revenue_monthly_prorated = lead['amount'] * probability / 100

                inserts.append({
                    'salesforce_lead_id': lead['id'],
                    'email_normalized': tools.email_normalize(lead['email_from']) or lead['email_from'],
                    'name': lead['name'],
                    'user_id': mapped_user_partner_ids[lead['owner_email']] if lead['owner_email'] in mapped_user_partner_ids else None,
                    'description': lead['description'],
                    'type': lead['type'],
                    'stage_id': 1, # TODO implement logic based on flags
                    'recurring_revenue_monthly': lead['amount'],
                    'recurring_revenue': lead['amount'],
                    'recurring_revenue_monthly_prorated': recurring_revenue_monthly_prorated,
                    'date_closed': lead['closedate'] if lead['isclosed'] else None,
                    'date_action_last': lead['lastactivitydate'],
                    'day_close': abs((lead['closedate'] - lead['createddate'].date()).days) if lead['isclosed'] else 0,
                    'date_open': lead['date_open'],
                    'day_open': abs((lead['date_open'] - lead['createddate']).days),
                    'date_conversion': lead['date_conversion'],
                    'date_deadline': lead['closedate'],
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'contact_name': contact_name,
                    'email_from': lead['email_from'],
                    'phone': lead['phone'],
                    'mobile': lead['mobilephone'],
                    'website': lead['website'],
                    'street': lead['street'],
                    'zip': lead['postalcode'],
                    'city': lead['city'],
                    'country_id': country_id,
                    'probability': probability,
                    'automated_probability': probability,
                    'create_date': lead['createddate'],
                    'create_uid': mapped_user_partner_ids[lead['createdby_email']] if lead['createdby_email'] in mapped_user_partner_ids else 1,
                    'cmp_source': lead['cmp_source__c'],
                    'cmp_medium': lead['cmp_medium__c'],
                    'cmp_name': lead['cmp_name__c'],
                    'cmp_term': lead['cmp_term__c'],
                    'cmp_content': lead['cmp_content__c'],
                    'cmp_campaign': lead['cmp_campaign__c'],
                    'facebookpage': lead['facebookseite__c'],
                    'date_last_stage_update': lead['systemmodstamp'],
                    'write_date': lead['lastmodifieddate'],
                })

                if lead['type__c'] == 'Partner':
                    new_tags.append(lead['id'])

        insert_query = """INSERT INTO crm_lead (
                        email_normalized, salesforce_lead_id, message_bounce,
                        name, user_id, company_id, description,
                        active, type, priority, team_id, stage_id, color, expected_revenue, prorated_revenue,
                        recurring_revenue, recurring_plan, recurring_revenue_monthly,
                        recurring_revenue_monthly_prorated, date_closed, date_action_last, date_open, day_open,
                        day_close, date_last_stage_update, date_conversion, date_deadline, partner_id, contact_name,
                        partner_name, function, title, email_from, phone, mobile, phone_state, email_state, website,
                        lang_id, street, zip, city, country_id, probability, automated_probability,
                        create_uid, create_date, write_uid, write_date,
                        cmp_source, cmp_medium, cmp_name, cmp_term, cmp_content, cmp_campaign,
                        facebookpage
                        )
        VALUES %s"""

        vals = [(i['email_normalized'], i['salesforce_lead_id'], 0,
                 i['name'], i['user_id'], 1, i['description'],
                 True, i['type'], 0, 1, i['stage_id'], 0, 0, 0,
                 i['recurring_revenue'], recurring_plan_ids[0].id, i['recurring_revenue_monthly'],
                 i['recurring_revenue_monthly_prorated'], i['date_closed'], i['date_action_last'], i['date_open'], i['day_open'],
                 i['day_close'], i['date_last_stage_update'], i['date_conversion'], i['date_deadline'], i['partner_id'], i['contact_name'],
                 i['partner_name'], None, None, i['email_from'], i['phone'], i['mobile'], None, None,  i['website'],
                 None, i['street'], i['zip'], i['city'], i['country_id'], i['probability'], i['automated_probability'],
                 i['create_uid'], i['create_date'], 1, i['write_date'],
                 i['cmp_source'], i['cmp_medium'], i['cmp_name'], i['cmp_term'], i['cmp_content'], i['cmp_campaign'], i['facebookpage']
                 ) for i in inserts]

        execute_values(self.env.cr, insert_query, vals)

        # Tags all leads with the proper categories
        # Creates the category if it does not exist
        if len(new_tags) > 1:
            lead_categories = self.env['crm.tag'].search([('name', '=', 'Partner')])
            if len(lead_categories) < 1:
                lead_categories = [self.env['crm.tag'].create({'name': 'Partner'})]

            new_tags_salesforce_lead_id_strings = ",".join([f"'{t}'" for t in new_tags])
            self.env.cr.execute(
                f"""INSERT INTO crm_tag_rel (lead_id, tag_id) SELECT id, {lead_categories[0].id} FROM crm_lead WHERE salesforce_lead_id IN ({new_tags_salesforce_lead_id_strings})""")


    @api.model
    def _sync_phonecalls(self):

        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()
        mapped_salesforce_task_ids = self._get_phone_calls_with_salesforce_task_id()

        cur.execute("""SELECT t.id, t.accountid, activitydate, calldisposition, calldurationinseconds, calltype,date_completed__c, LOWER(createdby.email) as createdby_email, t.createddate,
               t.description, entscheider_erreicht__c, isarchived, isclosed, t.lastmodifiedbyid,
               t.lastmodifieddate, nicht_erreicht__c, LOWER(owner.email) as owner_email, priority, reminderdatetime, status, subtype__c, subject, summary__c, t.systemmodstamp,
               tasksubtype, t.type, aircall__answered_by__c, aircall__call_recording__c, aircall__detailed_type__c, aircall__has_connected__c, aircall__hour_of_the_day__c,
               aircall__is_missed_call__c, aircall__is_voicemail__c, aircall__timezone__c, aircall__phone_number__c
               from task t
        LEFT JOIN user2 createdby on t.createdbyid = createdby.id
        LEFT JOIN user2 owner on t.ownerid = owner.id
        WHERE type = 'Call'""")

        calls = cur.fetchall()

        # update
        # create

        updates = []
        inserts = []

        for call in calls:
            if call['id'] in mapped_salesforce_task_ids:
                # TODO check which fields we want to take over
                # updates.append({
                #     'id': mapped_salesforce_account_ids[call['id']],
                #     'salesforce_account_id': call['id'],
                # })
                pass
            else:

                if call['isclosed'] and call['aircall__detailed_type__c'] in ('Outbound unanswered', 'Missed call', ):
                    state = 'cancel'
                elif call['isclosed']:
                    state = 'done'
                else:
                    state = 'open'

                inserts.append({
                    'salesforce_task_id': call['id'],
                    'create_date': call['createddate'],
                    'create_uid': mapped_user_partner_ids[call['createdby_email']] if call['createdby_email'] in mapped_user_partner_ids else 1,
                    'user_id': mapped_user_partner_ids[call['owner_email']] if call['owner_email'] in mapped_user_partner_ids else None,
                    'partner_id': mapped_salesforce_account_ids[call['accountid']]['id'] if call['accountid'] and call['accountid'] in mapped_salesforce_account_ids else None,
                    'description': call['description'],
                    'state': state,
                    'name': call['subject'],
                    'active': not call['isarchived'],
                    'duration': call['calldurationinseconds'] / 60.0 if call['calldurationinseconds'] is not None else 0,
                    'partner_phone': call['aircall__phone_number__c'],
                    'date': call['createddate'],
                    'direction': 'out' if call['calltype'] == 'Outbound' else 'in'
                })

        insert_query = """INSERT INTO crm_phonecall (create_date, user_id, partner_id, description,
                             state, name, active, duration, partner_phone,
                             priority, date, direction, create_uid, write_uid, write_date)

        VALUES %s"""

        vals = [(i['create_date'], i['user_id'], i['partner_id'], i['description'],
                 i['state'], i['name'], i['active'], i['duration'], i['partner_phone'],
                 0, i['date'], i['direction'], i['create_uid'], 1, datetime.datetime.now()) for i in inserts]

        execute_values(self.env.cr, insert_query, vals)


    @api.model
    def _sync_tasks(self):

        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()
        mapped_salesforce_task_ids = self._get_helpdesk_tickets_with_salesforce_task_id()

        cur.execute("""SELECT t.id, t.accountid, activitydate, date_completed__c, LOWER(createdby.email) as createdby_email, t.createddate,
               t.description, entscheider_erreicht__c, isarchived, isclosed, t.isdeleted, ishighpriority, isreminderset, t.lastmodifiedbyid,
               t.lastmodifieddate, nicht_erreicht__c, LOWER(owner.email) as owner_email, priority, reminderdatetime, status, subtype__c, subject, summary__c, t.systemmodstamp,
               tasksubtype, t.type
               from task t
        LEFT JOIN user2 createdby on t.createdbyid = createdby.id
        LEFT JOIN user2 owner on t.ownerid = owner.id
        WHERE type != 'Call' OR type IS NULL""")

        tasks = cur.fetchall()

        # update
        # create

        updates = []
        inserts = []
        activities = []

        for task in tasks:
            if task['id'] in mapped_salesforce_task_ids:
                # TODO check which fields we want to take over
                # updates.append({
                #     'id': mapped_salesforce_account_ids[task['id']],
                #     'salesforce_account_id': task['id'],
                # })
                pass
            else:

                partner_id = None
                partner_name = None
                if task['accountid'] and task['accountid'] in mapped_salesforce_account_ids:
                    partner_id = mapped_salesforce_account_ids[task['accountid']]['id']
                    partner_name = mapped_salesforce_account_ids[task['accountid']]['name']

                # user_id may not be null, so lets create a fallback to create_uid
                create_uid = mapped_user_partner_ids[task['createdby_email']] if task['createdby_email'] in mapped_user_partner_ids else 1
                if task['owner_email'] in mapped_user_partner_ids:
                    user_id = mapped_user_partner_ids[task['owner_email']]
                else:
                    user_id = create_uid

                new_task = {
                    'salesforce_task_id': task['id'],
                    'name': task['subject'] or task['id'],
                    'description': task['description'],
                    'active': not task['isarchived'] and not task['isdeleted'],
                    'user_id': user_id,
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'partner_email': None, # TODO check where to get the email from without parsing the content
                    'stage_id': 1,  # TODO implement logic based on flags
                    'date_last_stage_update': task['lastmodifieddate'],
                    'assign_date': task['createddate'],
                    'access_token': str(uuid.uuid4()),
                    'create_uid': create_uid,
                    'create_date': task['createddate'],
                    'write_date': task['lastmodifieddate'],
                    'reminderdatetime': task['reminderdatetime'],
                }
                inserts.append(new_task)
                if task['reminderdatetime'] is not None and task['reminderdatetime'] > datetime.datetime.now():
                    activities.append(new_task)



        insert_query = """INSERT INTO helpdesk_ticket (name, description, active, kanban_state,
                               user_id, partner_id, partner_name, partner_email, priority, stage_id,
                               date_last_stage_update, assign_date, assign_hours, close_hours,
                               sla_reached_late, rating_last_value, access_token, create_uid, create_date,
                               write_uid, write_date, salesforce_task_id)

        VALUES %s"""

        vals = [(i['name'], i['description'], i['active'], 'normal',
                 i['user_id'], i['partner_id'], i['partner_name'], i['partner_email'], 0, i['stage_id'],
                 i['date_last_stage_update'], i['assign_date'], 0, 0,
                 False, 0, i['access_token'], i['create_uid'], i['create_date'],
                 1, i['write_date'], i['salesforce_task_id']) for i in inserts]

        execute_values(self.env.cr, insert_query, vals)

        if len(activities) > 0:
            helpdesk_ticket_model_id = self.env['ir.model'].search([('model', '=', 'helpdesk.ticket')], limit=1).id
            mail_activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1).id

            for activity in activities:
                ticket = self.env['helpdesk.ticket'].search([('salesforce_task_id', '=', activity['salesforce_task_id'])])
                self.env['mail.activity'].create({
                    'activity_type_id': mail_activity_type_id,
                    'date_deadline': activity['reminderdatetime'].date(),
                    'recommended_activity_type_id': False,
                    'res_id': ticket.id,
                    'res_model_id': helpdesk_ticket_model_id,
                    'summary': ticket.name,
                    'user_id': activity['user_id'],
                })

                # self.env['calendar.event'].create({
                #     'name': ticket.name,
                #     'activity_ids': [(6, False, activity_id.ids)],
                #     'start': '2018-11-12 21:00:00',
                #     'stop': '2018-11-13 00:00:00',
                # })

    def _sync_from_salesforce(self):

        self._sync_companies_from_salesforce()
        self._sync_contacts_from_salesforce()

        self._sync_leads_and_opportunities()
        self._sync_phonecalls()
        self._sync_tasks()






