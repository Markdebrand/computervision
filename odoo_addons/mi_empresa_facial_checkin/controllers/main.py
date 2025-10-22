# -*- coding: utf-8 -*-
import odoo.http as http
from odoo.http import request
import requests


class FacialCheckinController(http.Controller):

    @http.route('/hr/attendance/facial_check', type='json', auth='user', csrf=False)
    def handle_facial_check(self, image_base64=None, latitude=None, longitude=None, **kwargs):
        # Validaciones básicas
        if not image_base64:
            return {'error': 'No se recibió imagen.'}
        if latitude is None or longitude is None:
            return {'error': 'No se recibió geolocalización.'}

        employee = request.env.user.employee_id
        if not employee:
            return {'error': 'No eres un empleado enlazado.'}

        if not employee.x_face_encoding:
            return {'error': 'No tienes un rostro registrado. Contacta a RRHH.'}

        # Llamar al microservicio de IA (ajusta la URL según despliegue)
        IA_API_URL = request.env['ir.config_parameter'].sudo().get_param(
            'mi_empresa_facial_checkin.ia_api_url',
            default='http://localhost:8000/verify_face'
        )
        try:
            response = requests.post(IA_API_URL, json={
                'image_b64': image_base64,
                'encoding_reference': employee.x_face_encoding
            }, timeout=10)

            if response.status_code != 200:
                return {'error': f'Error del servicio de IA (HTTP {response.status_code}).'}

            resp_json = response.json()
            if not resp_json.get('match'):
                return {'error': 'Rostro no coincide. Intenta de nuevo.'}

        except requests.RequestException as e:
            return {'error': f'Error conectando al servicio de IA: {e}'}

        # Crear/alternar fichaje estándar
        attendance = employee._attendance_action_change()

        # Guardar datos extra (GPS y foto) limpiando prefijo base64 si existe
        image_b64_clean = image_base64.split(',')[-1]
        if attendance.check_out:
            attendance.write({
                'x_checkout_latitude': latitude,
                'x_checkout_longitude': longitude,
                'x_checkout_snapshot': image_b64_clean,
            })
        else:
            attendance.write({
                'x_checkin_latitude': latitude,
                'x_checkin_longitude': longitude,
                'x_checkin_snapshot': image_b64_clean,
            })

        return {'success': True, 'attendance_id': attendance.id}
