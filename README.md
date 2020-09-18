# commonhealth-data-map-arcgis
  A CommonHealth data map hosted on ArcGIS Online.
  
## Script Execution Status
  ![JHU Covid19 Time Series Data Sync ](https://github.com/the-commons-project/commonhealth-data-map-arcgis/workflows/JHU%20Covid19%20Time%20Series%20Data%20Sync/badge.svg)

  ![Google Mobility Data Sync for EAC ](https://github.com/the-commons-project/commonhealth-data-map-arcgis/workflows/Google%20Mobility%20Data%20Sync%20for%20EAC/badge.svg)

  ![WHO Health Facility Data Sync for EAC ](https://github.com/the-commons-project/commonhealth-data-map-arcgis/workflows/WHO%20Health%20Facility%20Data%20Sync%20for%20EAC/badge.svg)



## DataProcessing

“DataProcessing/Scripts” folder in the repository contains Data processing scripts that read various data sources and save data to ArcGIS Online Hosted Feature Services.

  ### ArcGIS_Covid19_TimeSeries_DataSync.py:
  A python script to read data from COVID-19 Data Repository by the Center for Systems Science and Engineering (CSSE) at Johns Hopkins University on GitHub. The CSV data is processed to a custom data model to serve the information in ArcGIS dashboard.
  ### ArcGIS_HealthFacility_DataSync.py:
  A python script to read data from master list of health facilities was developed from a variety of government and non-government sources hosted in TCP common health data map ArcGIS GitHub repository. The CSV data is processed to a custom data model to serve the information in ArcGIS dashboard.
  ### ArcGIS_Mobility_DataSync.py
  A python script to read data from google community mobility. The Google Community Mobility Report is broken down by location and displays the change in visits to places like grocery stores and parks. The CSV data is processed to a custom data model to serve the information in ArcGIS dashboard.

## .github/workflows

“.github/workflows” folder in the repository contains GitHub Action scripts
  ### ArcGIS_Covid19_TimeSeries_Sync.yml: 
  Workflow setup to run ArcGIS_Covid19_TimeSeries_DataSync.py script every day (once a day) 5:30 AM UTC 
  ### ArcGIS_HealthFacility_DataSync.yml:
  Workflow setup to run ArcGIS_HealthFacility_DataSync.py script every month (once a month) 12:00 AM UTC
  ### ArcGIS_Mobility_DataSync.yml:
  Workflow setup to run ArcGIS_Mobility_DataSync.py script every Monday (once a week) 1 AM UTC
  
## Dashboard & ArcGIS Hosted Feature Services
  The application uses ArcGIS Online Platform and all the data application uses are ArcGIS Hosted Feature Services. Service Definitions, Views and Webmaps are all saved into CommonHealthDataMap folder. ArcGIS Dashboard for Desktop and mobile are configured and are accessible from the same folder.

## Web App wrapper
  Web App is a wrapper to host Desktop and Mobile versions of dashboard with a single access point URL and load the necessary dashboard based on the device the application is being loaded. 

## Steps to Deploy
  - App is deployed to GitHub Pages. Any changes to the deployment can be done from **Repository> Settings > GitHub Pages(section)**.
  - Steps to setup custom domain are provided in GitHub documentation at below mentioned path: 
  https://docs.github.com/en/github/working-with-github-pages/configuring-a-custom-domain-for-your-github-pages-site
  - Once the GitHub repository is setup, pushing new code to prod branch will deploy the application to live (https://covicheck.eac.int). 



