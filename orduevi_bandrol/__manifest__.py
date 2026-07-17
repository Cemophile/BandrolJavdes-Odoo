# -*- coding: utf-8 -*-
{
    'name': 'TSK Orduevi Bandrol Yönetimi',
    'version': '17.0.1.0.0',
    'summary': 'Emekli TSK Personeli Çevrimiçi Bandrol Satış ve Ödeme Otomasyonu',
    'description': """
TSK Bandrol Projesi
    """,
    'category': 'Services',
    'author': 'Proje Ekibi',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'mail'],
    'data': [
        'security/orduevi_security.xml',
        'security/ir.model.access.csv',
        'views/orduevi_bandrol_views.xml',
        'views/orduevi_transaction_views.xml',
        'views/orduevi_menus.xml',
        'data/demo_data.xml',
        'views/frontend_templates.xml',
        #'data/update_language.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'orduevi_bandrol/static/src/css/hide_apps_menu.css',
        ],
        'web.assets_frontend': [
            'orduevi_bandrol/static/src/css/hide_frontend_menu.css',
        ],
        'web.assets_backend': [
                    'orduevi_bandrol/static/src/js/bandrol_refresh.js',
                ],
    },
    'installable': True,
    'application': True,
}
