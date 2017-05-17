from locust import HttpLocust, TaskSet, task
import random
import resource
resource.setrlimit(resource.RLIMIT_NOFILE, (99999, 99999))

chars = list('-abcdefghijklmnopqrstuvwxyz1234567890-abcdefghijklmnopqrstuvwxyz1234567890-')

class WebsiteTasks(TaskSet):
    #def on_start(self):
    #     self.client.post("/rest/v2/passwordlogin", {
    #         "username": "18621623915",
    #         "password": "2016xiaoluyear"
    #     })
    
    def genData(self):
        return {
            'platform': 'android',
            'device_id': ''.join(random.sample(chars,36)),
            'regid':'d//igwEhgBGCI2TG6lWqlO82fL14QglJcMxBww66GtgQwPULe/KEMFZz5CEEcX4+9n/ZR9asIxt7s+9awGswOS//iq9ualI0TEdzeam/8VQ='
        }

    # @task
    def profile(self):
        self.client.get(
            "/rest/v1/users/profile",
            #cookies={' Hm_lvt_f8a445bf4aa2309eb173c6ad194dd6e7': '', ' Hm_lpvt_f8a445bf4aa2309eb173c6ad194dd6e7': '1472090342', ' _ga': 'GA1.2.894590665.1467259597', ' sessionid': 'tv33fjhjilfz697lmgox26opkae41596', ' Hm_lvt_b311e9cda9474b2df9ecb6fca89661db': '1455543328', ' csrftoken': 'VsLpY000cb0topeYsPXsOEZH4JEEYu5z', 'Hm_lvt_41f0054e0c010bb5da26ed87bc5aa249': '1455523180'}
        )

    @task
    def productdetail(self):
        product = random.randint(17050, 17088)
        self.client.get(
            "/rest/v2/modelproducts/%s"%product,
            # cookies={' Hm_lvt_f8a445bf4aa2309eb173c6ad194dd6e7': '', ' Hm_lpvt_f8a445bf4aa2309eb173c6ad194dd6e7': '1472090342', ' _ga': 'GA1.2.894590665.1467259597', ' sessionid': 'tv33fjhjilfz697lmgox26opkae41596', ' Hm_lvt_b311e9cda9474b2df9ecb6fca89661db': '1455543328', ' csrftoken': 'VsLpY000cb0topeYsPXsOEZH4JEEYu5z', 'Hm_lvt_41f0054e0c010bb5da26ed87bc5aa249': '1455523180'}
        )

    #@task
    def portal(self):
        self.client.get("/rest/v1/portal")
        
    #@task
    def set_device(self):
        self.client.post("/rest/v1/push/set_device",self.genData()) #cookies={'lang': 'en-US', ' user_sess': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjEuNDU5NzU4NTMyZSswOSwidGV4dCI6Im1laXhxaGkiLCJ0eXBlIjoic2VzcyJ9.Ec0p9a-rhJA8N5B5Rsis7SEb9OEIdvidyNPMEYKWhVc', ' Hm_lvt_f8a445bf4aa2309eb173c6ad194dd6e7': '1469866478,1470885341', ' Hm_lpvt_f8a445bf4aa2309eb173c6ad194dd6e7': '1470885341', ' _ga': 'GA1.2.44673081.1465226632', ' sessionid': '88072agy0gk1jsi7ppmt8wlko89venhz', ' user_last': 'xiaolumm/xiaolusys', ' Hm_lvt_b311e9cda9474b2df9ecb6fca89661db': '1460191894', ' csrftoken': 'mpMghvEmzYDHHt9uAI0nIUqyf9TEx6hZ', ' _gat': '1'})
         
 
class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    min_wait = 5000
    max_wait = 5000
