# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import AccessError


class OrdueviTransaction(models.Model):
    _name = 'orduevi.transaction'
    _description = 'Bandrol Satış / Ödeme İşlemi'
    _order = 'create_date desc'
    _rec_name = 'pos_siparis_no'

    def export_data(self, fields_to_export):
        # Export engeli
        raise AccessError(
            "Güvenlik İhlali: Bu tablodan veriyi dışarı aktarmak güvenlik politikaları gereği engellenmiştir.")

    pos_siparis_no = fields.Char(
        string='POS Sipariş No', copy=False,
        help='Sanal POS\'a gönderilen benzersiz sipariş/sepet numarası.',
    )

    kullanici_hash = fields.Char(
        string='Kullanıcı Hash', required=True, index=True,
        help='KVKK kapsamında TC Kimlik No tutulmaz. Bunun yerine SHA-256 ile şifrelenmiş hash değeri tutulur.'
    )

    bandrol_id = fields.Many2one(
        comodel_name='orduevi.bandrol', string='Bandrol Tipi', required=True,
    )
    pos_ref_kodu = fields.Char(
        string='POS Referans Kodu',
    )
    paket_suresi = fields.Selection([
        ('1', '1 Yıl'),
        ('3', '3 Yıl'),
        ('5', '5 Yıl')
    ], string="Paket Süresi", required=True, default='1')

    tutar = fields.Float(
        string='Tutar', compute='_compute_tutar', store=True, readonly=True,
    )

    durum = fields.Selection(
        selection=[('beklemede', 'Beklemede'), ('basarili', 'Başarılı'), ('hata', 'Hata')],
        string='Durum', required=True, default='beklemede',
    )
    harici_islem_token = fields.Char(
        string='Harici İşlem Token', required=True,
    )
    tarih = fields.Datetime(string='İşlem Tarihi', default=fields.Datetime.now, readonly=True)
    is_locked = fields.Boolean(
        string='Kilitli', compute='_compute_is_locked', store=True,
    )

    _sql_constraints = [
        ('pos_siparis_no_unique', 'unique(pos_siparis_no)',
         'Bu POS sipariş numarası ile zaten bir işlem mevcut!'),
    ]

    @api.depends('durum')
    def _compute_is_locked(self):
        for rec in self:
            rec.is_locked = rec.durum == 'basarili'

    @api.depends('bandrol_id', 'bandrol_id.ucret', 'paket_suresi')
    def _compute_tutar(self):
        for rec in self:
            if rec.bandrol_id and rec.paket_suresi:
                rec.tutar = rec.bandrol_id.ucret * int(rec.paket_suresi)
            else:
                rec.tutar = 0.0

    @api.constrains('paket_suresi')
    def _check_paket_suresi(self):
        allowed = {'1', '3', '5'}
        for rec in self:
            if rec.paket_suresi not in allowed:
                raise ValidationError(_('Paket süresi yalnızca 1, 3 veya 5 yıl olabilir.'))

    @api.constrains('bandrol_id')
    def _check_bandrol_yil(self):
        current_year = date.today().year
        for rec in self:
            if rec.bandrol_id and rec.bandrol_id.yil < current_year:
                raise ValidationError(_(
                    'Geçmiş yıla ait bir bandrol için işlem oluşturulamaz.'
                ))

    def write(self, vals):
        for rec in self:
            if rec.is_locked and not self.env.is_superuser():
                raise UserError(_(
                    'Bu işlem "Başarılı" durumuna geçtiği için kilitlenmiştir.'
                ))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.durum == 'basarili':
                raise UserError('Başarılı durumdaki bir işlem silinemez.')
        return super(OrdueviTransaction, self).unlink()