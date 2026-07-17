# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OrdueviBandrol(models.Model):

    _name = 'orduevi.bandrol'
    _description = 'Bandrol Tipi Tanımı'
    _order = 'yil desc, statu, kapsam'
    _rec_name = 'bandrol_id'

    bandrol_id = fields.Char(
        string='Bandrol Kodu', required=True, copy=False,
        help='Sistemin ana tanımlayıcısıdır (Örn: 2026-SUBAY).',
    )
    yil = fields.Integer(string='Yıl', required=True,
                          help='Bandrol tipinin geçerli olduğu yıl.')
    statu = fields.Selection(
        selection=[
            ('subay', 'Subay'),
            ('astsubay', 'Astsubay'),
            ('general', 'General'),
        ],
        string='Askeri Statü', required=True,
    )
    kapsam = fields.Selection(
        selection=[
            ('kendisi', 'Kendisi'),
            ('es', 'Eş'),
            ('cocuk', 'Çocuk'),
            ('anne', 'Anne'),
            ('baba', 'Baba'),
            ('kardes', 'Kardeş'),
        ],
        string='Kapsam', required=True,
        help='Bandrolün kapsadığı kitle. İleride yeni aile fertleri eklenebilir.',
    )
    ucret = fields.Float(
        string='Baz Fiyat (1 Yıllık)', required=True,
        help='Bu bandrol tipi için belirlenen baz fiyat.',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('bandrol_id_unique', 'unique(bandrol_id)',
         'Bu bandrol kodu ile zaten bir kayıt mevcut!'),
    ]

    @api.constrains('yil')
    def _check_yil(self):
        current_year = date.today().year
        for rec in self:
            if rec.yil and rec.yil < current_year:
                raise ValidationError(_(
                    'Bandrol geçerlilik yılı geçmiş bir yıl olarak seçilemez '
                    '(yıl >= %s olmalıdır).'
                ) % current_year)

    @api.constrains('ucret')
    def _check_ucret(self):
        for rec in self:
            if rec.ucret <= 0:
                raise ValidationError(_('Bandrol ücreti sıfırdan büyük olmalıdır.'))
