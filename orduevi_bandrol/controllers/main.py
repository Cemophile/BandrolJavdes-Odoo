# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from markupsafe import Markup
import iyzipay
import json
import hashlib
from datetime import date

class BandrolFrontend(http.Controller):

    def _msb_personel_servisini_sorgula(self, tc_kimlik):
        """
        Dış Kurum (MSB) Personel Servisi Mock
        İleride burası gerçek bir API isteğine dönüştürülmeli.
        """
        mock_api_response = {
            '11111111110': {'statu': 'subay', 'sicil_no': '2025-İS.25'},
            '22222222220': {'statu': 'astsubay', 'sicil_no': '2024-MUH.12'},
            '33333333330': {'statu': 'general', 'sicil_no': '2020-P.1'},
            '44444444440': {'statu': 'general', 'sicil_no': '2019-P.2'},

            # --- SUBAYLAR ---
            '10000000001': {'statu': 'subay', 'sicil_no': '2018-P.101'},
            '10000000002': {'statu': 'subay', 'sicil_no': '2015-TOP.34'},
            '10000000003': {'statu': 'subay', 'sicil_no': '2021-HV.88'},

            # --- ASTSUBAYLAR---
            '20000000001': {'statu': 'astsubay', 'sicil_no': '2019-BKM.55'},
            '20000000002': {'statu': 'astsubay', 'sicil_no': '2020-ULS.12'},
            '20000000003': {'statu': 'astsubay', 'sicil_no': '2022-DZ.99'},

            # Kucuk harfli sicilno
            '50000000001': {'statu': 'subay', 'sicil_no': '2022-is.45'},
            '50000000002': {'statu': 'astsubay', 'sicil_no': '2017-muh.112'}
        }

        return mock_api_response.get(tc_kimlik)


    @http.route('/', type='http', auth='public', website=True)
    def anasayfa_yonlendir(self, **kwargs):
        return request.redirect('/bandrol')


    @http.route('/bandrol', type='http', auth='public', website=True)
    def bandrol_sorgulama_sayfasi(self, **kwargs):
        return request.render('orduevi_bandrol.page_sorgulama', {})


    @http.route('/bandrol/islem', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def bandrol_islem(self, **post):
        # Güvenlik ve temizlik: Kullanıcı boşluklu yazarsa .strip() ile temizliyoruz
        tc_kimlik = post.get('tc_kimlik', '').strip()
        sicil_no = post.get('sicil_no', '').strip()

        # Kontroller
        if not tc_kimlik or not sicil_no:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'Lütfen T.C. Kimlik numaranızı ve Sicil Numaranızı giriniz.'
            })

        if not tc_kimlik.isdigit() or len(tc_kimlik) != 11:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'T.C. Kimlik Numarası 11 haneli olmalı ve sadece rakamlardan oluşmalıdır.'
            })

        tc_hash = hashlib.sha256(tc_kimlik.encode('utf-8')).hexdigest()

        # DIŞ SERVİS
        personel_servis_verisi = self._msb_personel_servisini_sorgula(tc_kimlik)

        if not personel_servis_verisi:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'Girdiğiniz T.C. Kimlik Numarası MSB tarafından doğrulanamadı.'
            })

        gelen_sicil = personel_servis_verisi.get('sicil_no', '').strip().upper()
        girilen_sicil = sicil_no.upper()

        if gelen_sicil != girilen_sicil:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'Girilen Sicil Numarası sistemdeki kayıtlarla eşleşmiyor.'
            })

        # Bandrol fiyat kontrolleri
        servisten_gelen_statu = personel_servis_verisi.get('statu')

        bandrol_kaydi = request.env['orduevi.bandrol'].sudo().search([
            ('statu', '=', servisten_gelen_statu)
        ], limit=1, order='yil desc')

        if not bandrol_kaydi:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'Statünüze uygun tanımlı bir bandrol fiyatlandırması bulunamadı.'
            })

        current_year = date.today().year

        mevcut_islem = request.env['orduevi.transaction'].sudo().search([
            ('kullanici_hash', '=', tc_hash),
            ('durum', '=', 'basarili'),
            ('bandrol_id.yil', '=', current_year)
        ], limit=1)

        if mevcut_islem:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': f'Sistem kayıtlarımıza göre {current_year} yılına ait bandrol ödemeniz zaten yapılmıştır.'
            })

        # IYZICO SANAL pos
        options = {
            'api_key': 'sandbox-aAlEhLQx7EiPgwBTU9iNrHOdCOBShxgJ',
            'secret_key': 'sandbox-ikWpoCIlRSfP49pK2PV9BsJDPv1blzhc',
            'base_url': 'sandbox-api.iyzipay.com'
        }

        request_payload = {
            'locale': 'tr',
            'conversationId': 'TRX_' + tc_hash[:10],
            'price': str(bandrol_kaydi.ucret),
            'paidPrice': str(bandrol_kaydi.ucret),
            'currency': 'TRY',
            'basketId': 'B' + str(bandrol_kaydi.id),
            'paymentGroup': 'PRODUCT',
            'callbackUrl': 'http://localhost:8069/bandrol/odeme_sonuc',
            'enabledInstallments': ['1'],
            'buyer': {
                'id': tc_hash[:10],
                'name': 'Askeri',
                'surname': 'Personel',
                'gsmNumber': '+905324000000',
                'email': 'personel@msb.gov.tr',
                'identityNumber': tc_kimlik,
                'lastLoginDate': '2023-01-01 12:43:35',
                'registrationDate': '2023-01-01 12:43:35',
                'registrationAddress': 'MSB Orduevi Tesisleri',
                'ip': request.httprequest.remote_addr,
                'city': 'Ankara',
                'country': 'Turkey',
                'zipCode': '06000'
            },
            'shippingAddress': {
                'contactName': 'Askeri Personel',
                'city': 'Ankara',
                'country': 'Turkey',
                'address': 'MSB Orduevi Tesisleri',
                'zipCode': '06000'
            },
            'billingAddress': {
                'contactName': 'Askeri Personel',
                'city': 'Ankara',
                'country': 'Turkey',
                'address': 'MSB Orduevi Tesisleri',
                'zipCode': '06000'
            },
            'basketItems': [
                {
                    'id': str(bandrol_kaydi.id),
                    'name': bandrol_kaydi.bandrol_id,
                    'category1': 'Bandrol',
                    'itemType': 'VIRTUAL',
                    'price': str(bandrol_kaydi.ucret)
                }
            ]
        }

        checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(request_payload, options)
        checkout_form_content = checkout_form_initialize.read().decode('utf-8')
        response_data = json.loads(checkout_form_content)

        iyzico_token = response_data.get('token')

        if iyzico_token:
            mevcut_bekleyen = request.env['orduevi.transaction'].sudo().search([
                ('kullanici_hash', '=', tc_hash),
                ('durum', '=', 'beklemede'),
                ('bandrol_id.yil', '=', current_year)
            ], limit=1)

            if mevcut_bekleyen:
                mevcut_bekleyen.sudo().write({
                    'harici_islem_token': iyzico_token,
                    'bandrol_id': bandrol_kaydi.id if bandrol_kaydi.exists() else False
                })
            else:
                request.env['orduevi.transaction'].sudo().create({
                    'kullanici_hash': tc_hash,
                    'bandrol_id': bandrol_kaydi.id if bandrol_kaydi.exists() else False,
                    'harici_islem_token': iyzico_token,
                    'durum': 'beklemede'
                })

        values = {
            'tc_kimlik': '***' + tc_kimlik[-2:],
            'bandrol_adi': bandrol_kaydi.bandrol_id,
            'statu_metni': dict(bandrol_kaydi._fields['statu'].selection).get(bandrol_kaydi.statu),
            'fiyat': bandrol_kaydi.ucret,
            'kapsam': dict(bandrol_kaydi._fields['kapsam'].selection).get(bandrol_kaydi.kapsam),
            'checkout_form': Markup(response_data.get('checkoutFormContent', 'POS Formu Yüklenemedi.'))
        }

        return request.render('orduevi_bandrol.page_odeme', values)


    @http.route('/bandrol/odeme_sonuc', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def bandrol_odeme_sonuc(self, **post):
        token = post.get('token')

        if not token:
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': 'İyzico ödeme belirteci (token) alınamadı.'
            })

        islem = request.env['orduevi.transaction'].sudo().search([
            ('harici_islem_token', '=', token)
        ], limit=1)

        options = {
            'api_key': 'sandbox-aAlEhLQx7EiPgwBTU9iNrHOdCOBShxgJ',
            'secret_key': 'sandbox-ikWpoCIlRSfP49pK2PV9BsJDPv1blzhc',
            'base_url': 'sandbox-api.iyzipay.com'
        }

        request_payload = {
            'locale': 'tr',
            'token': token
        }

        checkout_form_result = iyzipay.CheckoutForm().retrieve(request_payload, options)
        result_data = json.loads(checkout_form_result.read().decode('utf-8'))

        if result_data.get('paymentStatus') == 'SUCCESS':
            if islem:
                islem.sudo().write({
                    'pos_siparis_no': result_data.get('paymentId'),
                    'pos_ref_kodu': token,
                    'durum': 'basarili'
                })

                # --- CANLI GÜNCELLEME ---
                request.env['bus.bus'].sudo()._sendone('bandrol_islem_kanal', 'bandrol_guncelleme', 'yeni_satis')

                return request.render('orduevi_bandrol.page_dekont', {'islem': islem})
            else:
                return request.render('orduevi_bandrol.page_sorgulama', {
                    'error': 'Ödeme başarılı oldu ancak sistemde eşleşen işlem kaydı bulunamadı.'
                })
        else:
            if islem:
                islem.sudo().write({'durum': 'hata'})
            hata_mesaji = result_data.get('errorMessage',
                                          'Banka 3D Secure doğrulamasını reddetti veya işlem başarısız.')
            return request.render('orduevi_bandrol.page_sorgulama', {
                'error': f'Ödeme reddedildi: {hata_mesaji}'
            })