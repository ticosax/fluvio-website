#!/usr/bin/env python
import os
import json
from datetime import datetime
from fluvio import Fluvio, Offset

TOPIC_NAME = "patch-autosave"
PARTITION = 0

## push_patch: takes in a patch file generated by the autosave function, reads
## the patch file and wraps it in JSON before producing to the topic `patch-autosave`
def push_patch(file_patch):

    # convert the patch file to JSON
    object = {}
    object["time"] = "{}".format(datetime.now())
    object["patch"] = []
    with open(file_patch, "r") as patch:
        for line in patch:
            object["patch"].append(line)
    object_json = json.dumps(object)

    # connecting to fluvio cluster:
    fluvio = Fluvio.connect()

    # specifying what topic to produce to:
    producer = fluvio.topic_producer(TOPIC_NAME)
    # Fluvio.connect().topic_produce(<name of topic>):
    # Provides the topic in the fluvio database that you wish to store to.
    # In this case, the topic is patch-autosave.

    # sending the topic:
    producer.send_string(object_json)
    # Fluvio.connect().topic_produce(<name of topic>).send_string(<string>):
    # Stores <string> in a buffer until flush() is called to transmit it.
    # In this case, the string is a JSON object.

    # flusing the topic buffer:
    producer.flush()
    # Fluvio.connect().topic_produce(<name of topic>).flush():
    # Flushes the buffer and sends the stored content to the remote fluvio database.


## pull_patch: consumes the last 5 objects from the topic `patch-autosave`.
## Maybe the people designing the rest of the code want to offer up an option
## of previous saves?
def pull_patch(file_patch):
    # the number of records to consume from the fluvio database:
    to_recover = 5

    json_lst = []

    # connecting to fluvio cluster:
    fluvio = Fluvio.connect()

    # specifying which topic and partition to consume from:
    consumer = fluvio.partition_consumer(TOPIC_NAME, PARTITION)
    # Fluvio.connect().partition_consumer(<topic name>, <partition number>):
    # Creates a consumer that is looking at the topic and partition specified.
    # In this case topic is patch-autosave, and the partition is 0.

    # consuming the last five topics stored in the database:

    record = consumer.stream(Offset.from_end(to_recover))
    # Fluvio.connect().partition_consumer(<topic>, <partition>).stream(Offset):
    # Continually consumes all objects in the Fluvio database.
    # In this case, the offset is set to the five most recent objects in
    # the database.

    # Warning: Currently there is no flag to terminate stream() when it
    # reaches the end of the available data. Currently it is advised to
    # not call the stream() as a loop if you do not want it to loop forever.

    # appending the last five items into:
    for i in range(1, 6):
        # append the records to json_lst:
        json_lst.append("{}".format(record.__next__().value_string()))
        # record.value_string():
        # Returns the UTF-8 string value of the record.


    object = json.loads(json_lst[-1])

    with open(file_patch, "w") as patch:
        for item in object["patch"]:
            patch.write(item)

    # the call to a fictional script that would merge the patch file into the
    # current file and open it:
    #merge_patch_file(file_patch)


if __name__ == "__main__":

    os.popen("fluvio topic create {}".format(TOPIC_NAME))

    # Connect to cluster
    fluvio = Fluvio.connect()

    # Produce to topic
    producer = fluvio.topic_producer(TOPIC_NAME)
    with open("test", "r") as file:
        for line in file:
            producer.send_string("{}".format(line))
        producer.flush()


    # run the two scripts:
    push_patch("test")
    pull_patch("test2")

    # tests that the output of pull_patch equals the input of push_patch:
    with open("test", "r") as f1, open("test2", "r") as f2:
        for line1, line2 in zip(f1,f2):
            assert(line1 == line2), "file mismatch!"
