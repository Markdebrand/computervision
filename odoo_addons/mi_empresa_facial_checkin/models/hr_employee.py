# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Campo para guardar el vector numérico del rostro
    x_face_encoding = fields.Text('Codificación Facial')
    # Campo para guardar la foto de referencia (para auditoría)
    x_face_reference_image = fields.Binary('Foto de Referencia')
