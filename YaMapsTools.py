# https://github.com/zEvilCube/YandexMapTools

import requests
import sys
import math

MAP_SERVER = "http://static-maps.yandex.ru/1.x/"
GEO_SERVER = "http://geocode-maps.yandex.ru/1.x/"
ORG_SERVER = "https://search-maps.yandex.ru/v1/"

MAP_KEY = None  # Ключ для коммерческой версии Static API, если нужен.
GEO_KEY = ""    # Ключ к API Геокодера. Обязателен.
ORG_KEY = ""    # Ключ к API Поиска по организациям. Обязателен.


# Карта
def get_map_response(ll, _l="map", key=MAP_KEY, spn=None, z=None, size=None, scale=None,
                     pt=None, pl=None, lang="ru_Ru"):
    params = {"l": _l, "ll": ll, "key": key, "spn": spn, "z": z, "size": size, "scale": scale,
              "pt": pt, "pl": pl, "lang": lang
              }
    response = requests.get(MAP_SERVER, params=params)
    if not response:
        print("Ошибка в запросе:")
        print(response.url.replace('%2C', ','))
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    return response


# Топонимы объектов
def get_geo_toponyms(code, apikey=GEO_KEY, kind=None, rspn=None, ll=None, spn=None, bbox=None,
                     _format="json", lang="ru_RU", results=1, skip=None):
    params = {"apikey": apikey, "geocode": code, "kind": kind, "rspn": rspn, "ll": ll,
              "spn": spn, "bbox": bbox, "format": _format, "lang": lang,
              "results": results, "skip": skip}
    response = requests.get(GEO_SERVER, params=params)
    if not response:
        print("Ошибка в запросе:")
        print(response.url.replace('%2C', ','))
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    return response.json()["response"]["GeoObjectCollection"]["featureMember"]


# Топоним объекта под номером N
def get_geo_toponym(code, n=0, apikey=GEO_KEY, kind=None, rspn=None, ll=None, spn=None,
                    bbox=None, _format="json", lang="ru_RU"):
    toponyms = get_geo_toponyms(code, apikey=apikey, kind=kind, rspn=rspn, ll=ll, spn=spn, bbox=bbox,
                                _format=_format, lang=lang, results=n + 1, skip=n)
    return toponyms[n]["GeoObject"]


# Район объекта
def get_geo_district(coordinates):
    geo_toponym = get_geo_toponym(coordinates, kind='district')
    return geo_toponym['metaDataProperty']['GeocoderMetaData']['Address']['Components'][-1]['name']


# Координаты объекта
def get_geo_coordinates(toponym):
    lon, lat = map(float, toponym["Point"]["pos"].split())
    return lon, lat


# Границы объекта
def get_geo_borders(toponym):
    corners = toponym['boundedBy']['Envelope']
    lon1, lat1 = map(float, corners['lowerCorner'].split())
    lon2, lat2 = map(float, corners['upperCorner'].split())
    return lon1, lon2, lat1, lat2


# Размеры объекта
def get_geo_size(toponym):
    lon1, lon2, lat1, lat2 = get_geo_borders(toponym)
    return lon2 - lon1, lat2 - lat1


# Топонимы организаций
def get_org_toponyms(code, apikey=ORG_KEY, lang='ru_RU', _type='biz', ll=None,
                     spn=None, bbox=None, results=1, skip=None):
    ll_str = f'{str(ll[0])}, {str(ll[1])}'
    params = {"apikey": apikey, "text": code, "lang": lang, "type": _type, "ll": ll_str,
              "spn": spn, "bbox": bbox, "results": results, "skip": skip}
    response = requests.get(ORG_SERVER, params=params)
    if not response:
        print("Ошибка в запросе:")
        print(response.url.replace('%2C', ','))
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    return response.json()['features']


# Топоним организации под номером N
def get_org_toponym(code, n=0, apikey=ORG_KEY, lang='ru_RU', _type='biz', ll=None,
                    spn=None, bbox=None):
    toponyms = get_org_toponyms(code, apikey=apikey, lang=lang, _type=_type, ll=ll,
                                spn=spn, bbox=bbox, results=n + 1, skip=n)
    return toponyms[n]


# Координаты организации
def get_org_coordinates(toponym):
    lon, lat = toponym['geometry']['coordinates']
    return lon, lat


# Адрес организации
def get_org_address(toponym):
    return toponym['properties']['CompanyMetaData']['address']


# Название организации
def get_org_name(toponym):
    return toponym['properties']['CompanyMetaData']['name']


# Режим работы организации
def get_org_schedule(toponym):
    try:
        return toponym['properties']['CompanyMetaData']['Hours']['text']
    except Exception:
        return None


# Узнать, работает ли организация круглосуточно
def get_org_is_twenty_four_hours(toponym):
    try:
        avals = toponym['properties']['CompanyMetaData']['Hours']['Availabilities'][0]
        if 'TwentyFourHours' in avals.keys():
            return avals['TwentyFourHours']
        elif 'Intervals' in avals.keys():
            return False
    except Exception:
        pass
    return None


# Расстояние между двумя точками
def get_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b
    radians_lattitude = math.radians((a_lat + b_lat) / 2)
    lat_lon_factor = math.cos(radians_lattitude)
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    distance = math.sqrt(dx * dx + dy * dy)
    return int(distance)
