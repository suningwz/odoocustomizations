from odoo import api, fields, models, _, tools
import psycopg2
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
            ['id', 'salesforce_account_id'],
        )
        mapped_salesforce_account_ids = {}
        for p in partners_with_salesforce_account_ids:
            mapped_salesforce_account_ids[p['salesforce_account_id']] = p['id']

        return mapped_salesforce_account_ids

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

        return mapped_partner_ids

    def _sync_companies_from_salesforce(self, cur, mapped_country_ids, mapped_user_partner_ids):
        mapped_facility_ids = self._get_facility_id_partner_mapping()
        mapped_salesforce_account_ids = self._get_partners_with_salesforce_account_ids()

        cur.execute("""SELECT a.id, accountid__c, facility_id__c, active_mrr_c__c, backend_status__c, billingcity, billingcountry, billingpostalcode, billingstate, billingstreet, bitburger_kundennummer__c,
               LOWER(c.email) as createdby_email, a.createddate, customerstatusauto__c, dsgvo_gdor__c, email__c, facebookpage__c,  gesch_ftspartner__c,
               kaltakquise__c, language__c, masterrecordid, a.name, LOWER(o.email) as owner_email,    parentid, a.phone,recordtypeid, subscription_type__c,    vat_number__c, valid_payment_information__c, website,
               cmp_campaign__c,cmp_content__c, cmp_medium__c,  cmp_name__c, cmp_source__c,    cmp_term__c, mslatestcontractreasonfortermination__c, type__c, verified_admin__c
        FROM account a
        LEFT JOIN user2 c on a.createdbyid = c.id
        LEFT JOIN user2 o on a.ownerid = o.id
        LIMIT 10""")

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
    def _sync_from_salesforce(self):
        mapped_country_ids = self._get_country_ids_by_code()
        mapped_user_partner_ids = self._get_user_partner_ids_by_email()

        cur = self._create_db_cursor()

        self._sync_companies_from_salesforce(cur, mapped_country_ids, mapped_user_partner_ids)






