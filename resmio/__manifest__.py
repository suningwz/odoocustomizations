# -*- coding: utf-8 -*-
{
    'name' : 'resmio customizations',
    'description':"""
All customizations for resmio GmbH
=======================================
- Adds custom tempaltes
    """,
    'version' : '1.0',
    'category': 'Sales/CRM',
    'depends' : [
        'product',
        'l10n_de',
        'crm',
        'sale',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/crm_lead.xml',
        'views/din5008_report.xml',
        'views/product_template.xml',
        'views/report_invoice.xml',
        'views/res_config_settings_view.xml',
        'views/res_partner.xml',
        'views/sale_report_templates.xml'
    ]
}

