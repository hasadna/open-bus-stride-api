# Open Bus Stride API Usage Guide

This is a detailed guide to using the Stride API.

The Stride API uses standard REST and returns JSON objects, if you are familiar with such concepts feel free to skip this 
guide and head on to the API to start using it at https://open-bus-stride-api.hasadna.org.il/docs

First step is to find an API method you want to call. Head over to the API docs using your web browser at https://open-bus-stride-api.hasadna.org.il/docs

Some general details and useful links are displayed at the top, followed by a list of all the methods:

![image](https://user-images.githubusercontent.com/1198854/173553017-e6ed7554-ca6b-47af-bf02-20fc4860ed3c.png)

Click on an API method you want to use, for this example we will use the first one - `/route_timetable/list`. This will show all the parameters
for this method:

![image](https://user-images.githubusercontent.com/1198854/173553251-8f6d38c4-eff3-4b3e-83b9-5e52b8fd2848.png)

The API docs also allow to call functions directly from the web browser, click on the "Try it out" button.

Fill-in some of the fields, the fields have descriptions and you can also refer to the [Data Model](https://github.com/hasadna/open-bus-stride-db/blob/main/DATA_MODEL.md) 
and the [ETL Processes](https://github.com/hasadna/open-bus-pipelines/blob/main/STRIDE_ETL_PROCESSES.md) documentation for details regarding the
meaning of the fields.

Once you filled-in the required fields, click on the "Execute" button.

It will now show the request url:

![image](https://user-images.githubusercontent.com/1198854/173554017-0712ab08-fc40-4785-bd0b-b43b4bfc9ed8.png)

How to use this depends on your programming language, but in general, you will want to get just the domain and path part without the query string, 
for example:

```
https://open-bus-stride-api.hasadna.org.il/route_timetable/list
```

The query string and response parsing should be handled by your programming language HTTP library, 
for example, in Python using the Requests library it will look like this:

```
data = requests.get("https://open-bus-stride-api.hasadna.org.il/route_timetable/list", params={"get_count": "false", "line_refs": "5473232"}).json()
```

The `data` variable will now contain the result of this API method.
