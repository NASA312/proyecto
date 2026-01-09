from django import template
import decimal
import datetime
import json

register = template.Library()
excepciones = (
    'clave_soc',
    'num_socio_acreditado',
    'clave_suc',
    'sucursal',
    'no_socio',
    'anho',
    'anhio',
    'mes')

@register.filter
def to_underscore_title(value):
    return value.replace("_"," ")

@register.filter
def get_type(value, key="keyString"):
    exclude_validation_columns = ['clave_soc','num_socio_acreditado', 'no_cta', 'no_credito', 'no_cred', 'num_credito','dias', 'solicitud', 'numero_cred', 'folio_sol', 'clave_suc', 'tasa', 'dias_vencidos', 'anhio', 'mes']
    if type(value) == decimal.Decimal and key not in exclude_validation_columns:
        return 'numero'
    if type(value) == int:
        return 'int'
    if type(value) in (datetime.date, datetime.datetime):
        return 'fecha'
    if type(value) in (list, dict):
        return 'lista'
    return type(value)

@register.filter
def not_in_list(value,arg):
   return value not in arg

@register.filter
def in_list(value,arg):
   return value in arg

@register.filter('has_group')
def has_group(grupos, groups_name):
    """
    Verifica se este usuário pertence a un grupo
    """
    groups = groups_name.split(',')
    groups_user = grupos.split(',')



    if 'superuser' in groups_user :
        return True

    for group in groups:
        if group in groups_user:
            return  True

    return False

@register.filter('has_not_group')
def not_has_group(grupos, groups_name):
    """
    Verifica se este usuário no pertence a un grupo
    """
    groups = groups_name.split(',')
    groups_user = grupos.split(',')

    for group in groups:
        if group in groups_user:
            return False

    return False


@register.filter(name='split')
def split(value, arg):
    return value.split(arg)


@register.filter(name='split_cuenta')
def split(value, arg):
    return value.split(arg)[-1]

@register.filter
def to_json(value):
    """
    Filtro para convertir un objeto a JSON.
    """
    return json.dumps(value)

@register.filter
def get_ids(item, id_fields):
    """
    Extrae las IDs de un objeto basado en una lista de nombres de campos.
    """
    if not id_fields:
        return [item.get('ID')]  # ID por defecto si no se especifican campos
    return [item.get(field) for field in id_fields]

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_dict_values(dictionary, fields_str):
    fields = fields_str.split(',')
    return [dictionary.get(field, '') for field in fields]