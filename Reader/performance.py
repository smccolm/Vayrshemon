"""Every reading operation is timed; slow actions and UI stalls stay visible."""
from collections import deque
from datetime import datetime,timezone
from pathlib import Path
import json,os,time
from .storage import LOCAL

BUDGETS={'open':2500,'navigate':500,'pages':500,'palette':1500,'zoom':800,'fit':800,'pan':50,'search':500,'copy':500,'close':100,'paint':33,'heartbeat':50}

class Performance:
    def __init__(self):
        self.events=deque(maxlen=3000);self.path=LOCAL/'logs'/f'performance-{os.getpid()}.jsonl';self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('a',encoding='utf-8',buffering=1);self.slow=0
    def record(self,action,ms,**details):
        budget=BUDGETS.get(action,1000);slow=ms>budget
        event=dict(time=datetime.now(timezone.utc).isoformat(),action=action,ms=round(ms,3),budgetMs=budget,slow=slow,**details)
        self.events.append(event);self.slow+=int(slow)
        self.stream.write(json.dumps(event,ensure_ascii=True)+'\n')
        if self.stream.tell()>20*1024*1024:
            self.stream.close();old=self.path.with_suffix('.previous.jsonl');old.unlink(missing_ok=True);self.path.replace(old);self.stream=self.path.open('a',buffering=1,encoding='utf-8')
        return event
    def summary(self):
        grouped={}
        for e in self.events:grouped.setdefault(e['action'],[]).append(e['ms'])
        result={}
        for key,values in grouped.items():
            values.sort();result[key]=dict(count=len(values),medianMs=values[len(values)//2],p95Ms=values[min(len(values)-1,int(len(values)*.95))],maxMs=values[-1],budgetMs=BUDGETS.get(key,1000))
        return dict(actions=result,slowCount=self.slow,log=str(self.path))

