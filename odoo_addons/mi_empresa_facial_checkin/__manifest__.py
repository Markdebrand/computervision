{
    'name': 'Mi Empresa - Fichaje Facial',
    'version': '16.0.1.0.0',
    'summary': 'Añade reconocimiento facial y GPS al módulo de Asistencias.',
    'author': 'Tu Empresa',
    'license': 'LGPL-3',
    'category': 'Human Resources/Attendances',
    'depends': [
        'hr_attendance',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mi_empresa_facial_checkin/static/src/js/facial_checkin_widget.js',
            'mi_empresa_facial_checkin/static/src/css/facial_checkin.css',
            'mi_empresa_facial_checkin/static/src/xml/facial_checkin_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
}