import threading
import time
import queue
import requests

from lib.debugmodule import Log


class StreamScheduler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = queue.Queue()
        self.is_on = False
        self.is_running = False
        self.tag = 'SendThread'

    def run(self):
        """
        queue에 들어있는 send command 하나씩 꺼내서 url로 전송
        :return: none
        """
        while self.is_on:
            if self.is_running:
                if self.q.qsize() > 0:
                    # get one send command dict
                    send_cmd = self.q.get()

                    # validate send command
                    try:
                        url = send_cmd['url']
                        post_data = send_cmd['post_data']
                    except KeyError:
                        Log.e(self.tag, 'send command format error:', send_cmd)
                        continue

                    # send to backend server
                    send_error = True
                    while send_error:
                        try:
                            Log.d(self.tag, 'method: POST, url: ' + url)
                            Log.d(self.tag, 'body:', str(post_data)[:70], '...' if len(str(post_data)) > 70 else '')
                            response = requests.post(url, json=post_data)
                            send_error = False
                        except Exception as e:
                            Log.e(self.tag, 'http post error:', e.__class__.__name__)
                        finally:
                            try:
                                if response.status_code != 200:
                                    Log.e(self.tag, 'http post error: %d' % response.status_code)
                                    send_error = True
                            except:
                                Log.e(self.tag, 'no response.')
                                send_error = True
                            time.sleep(1)

            time.sleep(1)

    def start_thread(self):
        if not self.is_on:
            self.is_on = True
            self.is_running = True
            self.start()
        else:
            self.is_running = True
        Log.d(self.tag, 'controller started.')

    def pause_thread(self):
        if self.is_running:
            self.is_running = False
            Log.d(self.tag, 'controller paused.')

    def stop_thread(self):
        self.is_on = False
        Log.d(self.tag, 'controller stopped.')

    def put(self, d: dict):
        """
        send command를 queue에 삽입
        :param d: send command. :type: dict
            {
                'url': remote url,
                'post_data': CAS entry data
            }
        :return:
        """
        Log.d(self.tag, 'send command has been put in controller queue: ', str(d)[:30])
        self.q.put(d)

    def get(self):
        return self.q.get()
