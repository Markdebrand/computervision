# -*- coding: utf-8 -*-
from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Campos para el check-in
    x_checkin_latitude = fields.Float('Latitud (Check-In)', digits=(10, 7))
    x_checkin_longitude = fields.Float('Longitud (Check-In)', digits=(10, 7))
    x_checkin_snapshot = fields.Binary('Foto (Check-In)')

    # Campos para el check-out
    x_checkout_latitude = fields.Float('Latitud (Check-Out)', digits=(10, 7))
    x_checkout_longitude = fields.Float('Longitud (Check-Out)', digits=(10, 7))
    x_checkout_snapshot = fields.Binary('Foto (Check-Out)')
