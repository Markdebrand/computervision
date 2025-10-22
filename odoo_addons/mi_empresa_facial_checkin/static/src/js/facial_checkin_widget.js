odoo.define('mi_empresa_facial_checkin.FacialCheckinWidget', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const Dialog = require('web.Dialog');

    const _t = core._t;

    const FacialCheckinWidget = AbstractAction.extend({
        template: 'FacialCheckinKioskTemplate',
        events: {
            'click .o_facial_checkin_btn': '_onClickCheckIn',
        },

        // Acción principal al pulsar el botón
        _onClickCheckIn: function () {
            const self = this;
            this._getGPSLocation()
                .then(function (coords) {
                    return self._showCameraModal().then(function (imageBase64) {
                        return { imageBase64, coords };
                    });
                })
                .then(function ({ imageBase64, coords }) {
                    return self._sendDataToServer(imageBase64, coords.latitude, coords.longitude);
                })
                .catch(function (err) {
                    self.displayNotification({
                        type: 'warning',
                        title: _t('Fichaje Facial'),
                        message: err && err.message ? err.message : (err || _t('Error desconocido.')),
                    });
                });
        },

        // Geolocalización
        _getGPSLocation: function () {
            return new Promise((resolve, reject) => {
                if (!('geolocation' in navigator)) {
                    reject(_t('GPS no soportado por este navegador.'));
                    return;
                }
                navigator.geolocation.getCurrentPosition(
                    (position) => resolve(position.coords),
                    (error) => {
                        reject(_t('Permiso de GPS denegado o no disponible.'));
                    },
                    { timeout: 10000 }
                );
            });
        },

        // Modal de cámara con captura a canvas
        _showCameraModal: function () {
            const self = this;
            return new Promise(async function (resolve, reject) {
                if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
                    reject(_t('La cámara no es soportada en este navegador.'));
                    return;
                }

                let stream;
                const $content = $(
                    '<div class="o_facial_modal">\
                        <video class="o_facial_video" autoplay playsinline style="width:100%;max-height:60vh;background:#000"></video>\
                        <canvas class="o_facial_canvas" style="display:none;"></canvas>\
                    </div>'
                );

                const dialog = new Dialog(self, {
                    title: _t('Fichaje Facial - Cámara'),
                    size: 'medium',
                    $content: $content,
                    buttons: [
                        {
                            text: _t('Cancelar'),
                            close: true,
                            classes: 'btn-secondary',
                            click: function () {
                                if (stream) {
                                    stream.getTracks().forEach(t => t.stop());
                                }
                            },
                        },
                        {
                            text: _t('Capturar'),
                            classes: 'btn-primary',
                            click: function () {
                                try {
                                    const video = $content.find('.o_facial_video')[0];
                                    const canvas = $content.find('.o_facial_canvas')[0];
                                    const width = video.videoWidth || 640;
                                    const height = video.videoHeight || 480;
                                    canvas.width = width;
                                    canvas.height = height;
                                    const ctx = canvas.getContext('2d');
                                    ctx.drawImage(video, 0, 0, width, height);
                                    const dataURL = canvas.toDataURL('image/jpeg', 0.92);
                                    if (stream) {
                                        stream.getTracks().forEach(t => t.stop());
                                    }
                                    dialog.close();
                                    resolve(dataURL);
                                } catch (e) {
                                    reject(_t('No se pudo capturar la imagen.'));
                                }
                            },
                        },
                    ],
                });

                dialog.opened().then(async function () {
                    try {
                        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
                        const video = $content.find('.o_facial_video')[0];
                        video.srcObject = stream;
                        await video.play();
                    } catch (e) {
                        dialog.close();
                        reject(_t('Permiso de cámara denegado o no disponible.'));
                    }
                });

                dialog.open();
            });
        },

        // Enviar datos al backend
        _sendDataToServer: function (imageBase64, latitude, longitude) {
            const self = this;
            return rpc.query({
                route: '/hr/attendance/facial_check',
                params: {
                    image_base64: imageBase64,
                    latitude: latitude,
                    longitude: longitude,
                },
            }).then(function (result) {
                if (result && result.error) {
                    self.displayNotification({ type: 'warning', title: _t('Fichaje Facial'), message: result.error });
                } else {
                    self.displayNotification({ type: 'success', title: _t('Fichaje Facial'), message: _t('Fichaje registrado correctamente.') });
                    self.trigger_up('reload');
                }
            }).catch(function () {
                self.displayNotification({ type: 'danger', title: _t('Fichaje Facial'), message: _t('Error inesperado al registrar.') });
            });
        },
    });

    core.action_registry.add('hr_attendance_facial_checkin_kiosk', FacialCheckinWidget);
    return FacialCheckinWidget;
});