from typing import Dict

class EventObservable:
    __eventDict__: Dict[str, list] = dict()
    def addListener(self, eventName:str, eventHandler):
        evenHandletList = self.__eventDict__.get(eventName)
        if evenHandletList == None:
            evenHandletList = self.__eventDict__[eventName] = []
        evenHandletList.append(eventHandler)
        print(self.__eventDict__[eventName])

    def removeListener(self, eventName:str, eventHandler):
        evenHandletList = self.__eventDict__.get(eventName)
        evenHandletList.remove(eventHandler)

    def tiggerEvent(self, eventName:str, **kwargs):
        evenHandletList = self.__eventDict__.get(eventName)
        if not evenHandletList == None:
            for evenHandle in evenHandletList:
                evenHandle(eventName, **kwargs)