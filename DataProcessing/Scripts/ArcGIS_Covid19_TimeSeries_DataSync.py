from urllib import urlencode
from json import dumps as jsondumps
from json import loads as jsonloads
from datetime import datetime
import csv
import urllib
import urllib2
import sys


confirmed_csv_file = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
death_csv_file = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
recovered_csv_file = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
# country_list = {'Kenya': 'KE',  'Rwanda': 'RW', 'Tanzania': 'TZ', 'Uganda': 'UG', 'Burundi': 'BI',
#                 'South Sudan': 'SS'}

country_list = {'Kenya': {'Code': 'KE', 'OID': 2},  'Rwanda': {'Code': 'RW', 'OID': 4},
                'Tanzania': {'Code': 'TZ', 'OID': 6}, 'Uganda': {'Code': 'UG', 'OID': 1},
                'Burundi': {'Code': 'BI', 'OID': 3}, 'South Sudan': {'Code': 'SS', 'OID': 5}}

table_feature_server_url = 'https://services8.arcgis.com/jBR2I70Id8UqWlJI/arcgis/rest/services/EAC_COVID_TimeSeries/FeatureServer/1'
eac_feature_server_url = 'https://services8.arcgis.com/jBR2I70Id8UqWlJI/arcgis/rest/services/EAC_COVID_TimeSeries/FeatureServer/0'

table_fields = ["Country_name", "Country_code",  "category", "entry_date", "Category_count"]
epoch = datetime(1970, 1, 1)
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
        print token
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


def load_time_series_data(ip_record, token):
    """"
    Country_name, Country_code, entry_date, category, Category_count,
    """
    country = ip_record['Country/Region']  # The key will be change if CSV header changes
    country_code = country_list[country].get('Code')
    for key, value in ip_record.items():
        if key != 'Country/Region':
            confirm_new_record, death_new_record, recover_new_record, active_new_record = [], [], [], []
            date = key
            epoch_time = float((datetime.strptime(date, "%m/%d/%y") - epoch).total_seconds())*1000
            # count = value
            confirm_new_record = [country, country_code, 'Confirmed', epoch_time, value.get('Confirmed')]
            death_new_record = [country, country_code, 'Death', epoch_time, value.get('Death')]
            recover_new_record = [country, country_code, 'Recovered', epoch_time, value.get('Recovered')]
            active_new_record = [country, country_code, 'Active', epoch_time, value.get('Active')]
            featurejson = [{"attributes": dict(zip(table_fields[:], confirm_new_record[:]))},
                           {"attributes": dict(zip(table_fields[:], death_new_record[:]))},
                           {"attributes": dict(zip(table_fields[:], recover_new_record[:]))},
                           {"attributes": dict(zip(table_fields[:], active_new_record[:]))}]
            success, msg = writetoweblayer(url=table_feature_server_url, featureset=featurejson, token=token,
                                           operation="add")
            print success, country


def update_eac_country_data(latest_date, cases_data, country_name, token):
    epoch_time = float((datetime.strptime(latest_date, "%m/%d/%y") - epoch).total_seconds()) * 1000
    featurejson = [{"attributes": {"OBJECTID": country_list[country_name].get('OID'),
                                   "Country_name": country_name,
                                   "Country_code": country_list[country_name].get('Code'),
                                   "last_updated_date": epoch_time,
                                   "confirmed":cases_data['Confirmed'],
                                   "active": cases_data['Active'],
                                   "recovered": cases_data['Recovered'],
                                   "deceased": cases_data['Death']}}]
    success, msg, = writetoweblayer(url=eac_feature_server_url, featureset=featurejson, token=token, operation="update")
    # print featurejson
    if not success:
        print "Could not set aborted status to failed."
    else:
        print featurejson


def get_covid_data(csv_file_url, previous_process_date):
    response = urllib.urlopen(csv_file_url).read().decode('utf8').split("\n")
    reader = csv.reader(response)
    # csv_file = csv.writer(open(covid_cases_category + '.csv', 'w'))
    header = reader.next()
    province_idx = header.index('Province/State')
    lat_idx = header.index('Lat')
    long_idx = header.index('Long')
    ind2remove = [province_idx, lat_idx, long_idx]
    header_row = [x for i, x in enumerate(header) if i not in ind2remove]
    processed_data = {}
    for indx, line in enumerate(reader):
        if line:
            if indx == 0:
                pass
            elif line[1] in country_list.keys():
                data_row = [x for i, x in enumerate(line) if i not in ind2remove]
                # csv_file.writerow(data_row)
                record = dict(zip(header_row[:], data_row[:]))
                processed_data.update({record['Country/Region']: record})
    if previous_process_date is None:
        return processed_data
    else:
        data_dict = {}
        for key, value in processed_data.items():
            temp = {}
            for k, v in value.items():
                if k != 'Country/Region' and datetime.strptime(k, "%m/%d/%y") > datetime.strptime(previous_process_date, "%m/%d/%y"):
                    temp.update({k: v})
            data_dict.update({key: temp})
        return data_dict


def get_previous_data_processing_date(time_series_url, token):
    # remove trailing slash in url if any
    url = time_series_url[:-1] if time_series_url.endswith("/") else time_series_url
    # check if layerid is provided in url
    if not url[-1:].isdigit():
        raise Exception("LayerID missing in URL: {0}".format(url))
    url = url + '/query?where=1=1&outFields=entry_date&returnGeometry=false&returnIdsOnly=false&returnDistinctValues=true&f=json&token=' + token
    response = urllib.urlopen(url).read()
    print response
    output = jsonloads(response)
    if "error" in output:
        msg = output["error"]["message"]
        details = str("\n".join(output["error"]["details"]))
        return False, "{0}\n{1}".format(msg, details)
    elif not output.get("features"):
        return True, None
    else:
        date_set = [datetime.fromtimestamp(sub_dict.get("attributes").get("entry_date") / 1000).strftime('%m/%d/%y')
                    for sub_dict in output.get("features")]

        previous_max_date = max(date_set, key=lambda d: datetime.strptime(d, '%m/%d/%y'))
        return True, previous_max_date


def data_processing(confirmed_cases_data, death_case_data, recovered_cases_data, token):
    final_data = {}
    for country in country_list:
        final_data.update({'Country/Region': country})
        for key, value in confirmed_cases_data[country].items():
            if key != 'Country/Region':
                temp_dict = {}
                confirm_no = int(value)
                death_no = int(death_case_data[country].get(key))  # if key in death_case_data else 0
                recovered_no = int(recovered_cases_data[country].get(key))  # if key in recovered_cases_data else 0
                temp_dict.update({'Confirmed': confirm_no})
                temp_dict.update({'Death': death_no})
                temp_dict.update({'Recovered': recovered_no})
                active_no = confirm_no - (death_no + recovered_no)
                # TODO : Make negative number as zero
                temp_dict.update({'Active': active_no})
                final_data.update({key: temp_dict})
        # will give date list  from CSV data
        date_list = [item for item in final_data.keys() if item != 'Country/Region']
        max_date = max(date_list, key=lambda d: datetime.strptime(d, '%m/%d/%y'))
        print max_date, final_data[max_date]
        # update country latest day cases data
        update_eac_country_data(max_date, final_data[max_date], country, token)
        # TODO: Make uncomment and next time run it from previous days.
        load_time_series_data(final_data, token)

        
def truncate_mobility_data(table_feature_server_url, auth_token):
    # truncate or delete to mobility table
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
    token = get_token(tokenURL, username, password)
    
    # truncate or delete previous records
    truncate_mobility_data(table_feature_server_url, token)
    
    success, previous_process_date = get_previous_data_processing_date(table_feature_server_url, token)
    if success:
        print "Previous data processing done on '{}'".format(previous_process_date)
        print 'Fetching confirmed cases data....'
        confirmed_data = get_covid_data(confirmed_csv_file, previous_process_date)
        print 'Confirmed cases data is fetched...'

        print 'Fetching deceased cases data....'
        death_data = get_covid_data(death_csv_file, previous_process_date)
        print 'Deceased cases data is fetched....'

        print 'Fetching recovered cases data....'
        recovered_data = get_covid_data(recovered_csv_file, previous_process_date)
        print 'Recovered cases data is fetched....'
        print confirmed_data
        print death_data
        print recovered_data
        data_processing(confirmed_data, death_data, recovered_data, token)
        print('Done')
    else:
        print previous_process_date


if __name__ == '__main__':
    main()
