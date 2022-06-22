### Follow planned and real-time bus statistics 🚌

Welcome to The Public Knowledge Workshop's Stride project. We provide usable and accurate data about the Israeli public transportation system.

For background on the project and some more detailed documentation and usage guides, see [STRIDE.md](https://github.com/hasadna/open-bus-pipelines/blob/main/STRIDE.md).

Looking for a specific use-case?

* Take a look at the **user cases** APIs below.
* Try one of our existing [jupyter notebooks](https://github.com/hasadna/open-bus-stride-client/blob/main/README.md#using-the-interactive-jupyter-notebooks).
* Don't see your use-case covered here? Please [open us a ticket](https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fhasadna%2Fopen-bus%2Fissues%2Fnew)!

Queries are by default limited to 100 results per query, this limit can be increased up to 500,000 results.
Please try to set appropriate query parameters to limit the results to reduce load on our DB.
If you do need to get large number of results (up to 500,000) it's recommended to use one of these methods:

1. Use HTTP streaming and JSON streaming decoder, this method is most efficient and provide accurate results.
   Our [Stride Python Client iterate method](https://github.com/hasadna/open-bus-stride-client#usage) uses this method.
2. Use combination of limit / offset parameters to get results by page. This method may be less accurate because
   it depends on data remaining unchanged between requests.

For more advanced usage-

* Use **gtfs** for data about the planned lines timetables. 
* Use **siri** for data about lines real-time
* See [Open Bus Stride Data Model](https://github.com/hasadna/open-bus-stride-db/blob/main/DATA_MODEL.md) for description of field and table names.
* See [Open Bus Stride ETL Processes](https://github.com/hasadna/open-bus-pipelines/blob/main/STRIDE_ETL_PROCESSES.md) for description of the ETL processes which fetch and aggregate the data.
* See [MOT Developer Information](https://www.gov.il/BlobFolder/generalpage/gtfs_general_transit_feed_specifications/he/GTFS%20-%20Developer%20Information.pdf) for description of the source fields as published by the Israel Ministry of Transportation.
