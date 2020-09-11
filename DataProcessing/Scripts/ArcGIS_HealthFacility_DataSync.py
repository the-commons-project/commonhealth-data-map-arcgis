from urllib import urlencode
from json import dumps as jsondumps
from json import loads as jsonloads
from datetime import datetime
import csv
import urllib
import urllib2
import time
import sys
epoch = datetime(1970, 1, 1)

#https://raw.githubusercontent.com/the-commons-project/commonhealth-data-map-arcgis/master/DataProcessing/Data/who-cds-gmp-2019-01-eng-facilities.csv
#https://raw.githubusercontent.com/the-commons-project/commonhealth-data-map/develop/data-processing/data/who-cds-gmp-2019-01-eng-facilities.csv
health_facility_csv_url = r'https://covidcheck.eac.int/DataProcessing/Data/who-cds-gmp-2019-01-eng-facilities.csv'

health_facility_field = ['Country', 'Admin1', 'Facility_name', 'Facility_type', 'Ownership', 'Lat', 'Long_', 'LL_source']

health_facility_table_feature_server_url = r'https://services8.arcgis.com/jBR2I70Id8UqWlJI/arcgis/rest/services/EAC_Facilities/FeatureServer/2'

country_list = {'Kenya': {'Code': 'KE', 'OID': 2},  'Rwanda': {'Code': 'RW', 'OID': 4},
                'Tanzania': {'Code': 'TZ', 'OID': 6}, 'Uganda': {'Code': 'UG', 'OID': 1},
                'Burundi': {'Code': 'BI', 'OID': 3}, 'South Sudan': {'Code': 'SS', 'OID': 5}}

tokenURL = 'https://commongeo.maps.arcgis.com/sharing/rest/generateToken'
username = sys.argv[1]
password = sys.argv[2]
referer = 'https://commongeo.maps.arcgis.com'


def get_token(token_url, user_name, pass_word):
    """ use this to get a token from ArcGIS online """
    # payload params for the post request
    print("Generating ArcGIS Online authentication token.")
    params = {'f': 'pjson', 'username': user_name, 'password': pass_word,
              'referer': referer, 'expiration': 1440}
    data = urllib.urlencode(params)
    req = urllib2.Request(token_url, data)
    response = urllib2.urlopen(req)
    json_result = jsonloads(response.read())
    if 'token' in json_result:
        print('ArcGIS Online authentication token is generated.')
        token = json_result['token']
        return token
    else:
        print '{}: {}'.format(response.code, response.msg)
        return None


def writetoweblayer(url, featureset, token, operation=""):
    try:
        # remove trailing slash in url if any
        url = url[:-1] if url.endswith("/") else url
        # check if layerid is provided in url
        if not url[-1:].isdigit():
            raise Exception("LayerID missing in URL: {0}".format(url))
        if operation.lower() == "add":
            url = url + "/addFeatures?token=" + token
        elif operation.lower() == "update":
            url = url + "/updateFeatures?token=" + token
        elif operation.lower() == "delete":
            url = url + "/deleteFeatures?where=1=1&token=" + token
        else:
            raise Exception("Operation add/update not specified.")

        # prepare featureset to post
        if operation.lower() == "delete":
            payload = urlencode({"f": "json"})
            result = urllib.urlopen(url=url, data=payload).read()
        else:
            payload = urlencode({"features": jsondumps(featureset), "f": "json"})
            result = urllib.urlopen(url=url, data=payload).read()

        try:
            # check if json is returned
            result_json = jsonloads(result)
        except Exception as error:
            raise Exception("Operation {0} did not return valid JSON with error- {1} .".format(operation, error))

        # check if there are any errors returned from add features
        if result_json.has_key("error"):
            msg = result_json["error"]["message"]
            details = str("\n".join(result_json["error"]["details"]))
            return False, "{0}\n{1}".format(msg, details)
        resultkey = None
        if operation == "add":
            resultkey = "addResults"
        elif operation == "update":
            resultkey = "updateResults"
        elif operation == "delete":
            resultkey = "deleteResults"
        if resultkey in result_json:
            for rlt in result_json[resultkey]:
                if not rlt["success"]:
                    raise Exception("Writing feature failed.")
        return True, True
    except Exception as error:
        errmsg = str(error)
        return False, errmsg


def divide_chunks(main_list, chunk_size):
    for i in range(0, len(main_list), chunk_size):
        yield main_list[i:i+chunk_size]


def get_csv_data(csv_url, auth_token):
    start_time = time.time()
    response = urllib.urlopen(csv_url).read().split("\n")  # .decode('utf8').split("\n")
    print("--- %s seconds ---" % (time.time() - start_time))
    csv_reader = csv.DictReader(response)
    feature_json = []
    for line in csv_reader:
        try:
            country = line['Country']
            if country in country_list:
                # -- ['Country', 'Admin1', 'Facility_name', 'Facility_type', 'Ownership', 'Lat', 'Long_', 'LL_source']
                data_row = [line['Country'], line['Admin1'], line['Facility name'], line['Facility type'],
                            line['Ownership'], line['Lat'], line['Long'], line['LL source']]
                feature_json.append({"attributes": dict(zip(health_facility_field[:], data_row[:]))})
        except Exception as error:
            print error, line
    if feature_json:
        input_json_lists = list(divide_chunks(feature_json, 10))
        for featurejson in input_json_lists:
            # write to health facility table
            success, msg = writetoweblayer(url=health_facility_table_feature_server_url, featureset=featurejson,
                                           token=auth_token, operation="add")
            print success


def truncate_health_facility_data(table_feature_server_url, auth_token):
    # truncate or delete to health facility table
    if not table_feature_server_url[-1:].isdigit():
        raise Exception("LayerID missing in URL: {0}".format(table_feature_server_url))
    url = table_feature_server_url + '/query?where=1=1&returnGeometry=false&returnIdsOnly=true&f=json&token=' + auth_token
    response = urllib.urlopen(url).read()
    oid_ouptut = jsonloads(response)
    if "error" in oid_ouptut:
        msg = oid_ouptut["error"]["message"]
        details = str("\n".join(oid_ouptut["error"]["details"]))
        print False, "{0}\n{1}".format(msg, details)
    elif not oid_ouptut.get("objectIds"):
        pass
    else:
        oid_list = oid_ouptut.get("objectIds")
        feat_json = {'objectIds': oid_list, 'f': 'json'}
        success, msg = writetoweblayer(url=table_feature_server_url, featureset=feat_json,
                                       token=auth_token, operation="delete")


def main():
    # Generate ArcGIS Online Token
    token = get_token(tokenURL, username, password)
    # truncate or delete previous records
    truncate_health_facility_data(health_facility_table_feature_server_url, token)
    get_csv_data(health_facility_csv_url, token)


if __name__ == '__main__':
    main()
