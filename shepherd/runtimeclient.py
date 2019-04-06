import msgpackrpc


class RuntimeClient:
    def __init__(self, host, port):
        self.host, self.port, self.client = host, port, None

    def connect(self):
        self.client = msgpackrpc.Client(msgpackrpc.Address(self.host, self.port))

    def disconnect(self):
        self.client.close()
        self.client = None

    @property
    def connected(self):
        return self.client != None

    def set_mode(self, mode=True):
        self.client.call('set_mode', mode)

    def set_alliance(self, alliance):
        self.client.call('set_alliance', alliance)

    def set_master(self, master):
        self.client.call('set_master', master)

    def set_starting_zone(self, zone):
        self.client.call('set_starting_zone', zone)

    def run_challenge(self, seed, timeout=1):
        self.client.notify('run_challenge', int(seed), timeout)

    def get_challenge_solution(self):
        return self.client.call('get_challenge_solution')


class RuntimeClientManager:
    def __init__(self, blue_alliance, gold_alliance):
        self.blue_alliance, self.gold_alliance = blue_alliance, gold_alliance
        self.clients = {
            team: (RuntimeClient(f'192.168.128.{200 + team}', 6020) if team >= -100 else None)
            for team in self.blue_alliance + self.gold_alliance
        }
        for client in self.clients.values():
            if client is not None:
                 print(client.host)
                 client.connect()
        for team in self.blue_alliance:
            client = self.clients[team]
            if client:
                client.set_alliance('blue')
        for team in self.gold_alliance:
            client = self.clients[team]
            if client:
                client.set_alliance('gold')

    def set_starting_zones(self, zones):
        for team, zone in zip(self.blue_alliance + self.gold_alliance, zones):
            if self.clients[team]:
                self.clients[team].set_starting_zone(zone)

    def set_mode(self, mode):
        for client in self.clients.values():
            if client:
                print('Setting mode for client:', client.host)
                client.set_mode(mode)

    def get_challenge_solutions(self):
        return {team: (client.get_challenge_solution() if client else None) for team, client in self.clients.items()}

    def set_master_robots(self, blue_team, gold_team):
        """
        blue_master = self.clients[blue_team]
        if blue_master:
            blue_master.set_master()
        gold_master = self.clients[gold_team]
        if gold_master:
            gold_master.set_master()"""


client = RuntimeClient('192.168.128.115', 6020)
client.connect()
client.set_mode('idle')
# print('OK!')
# import time
# client.set_alliance('blue')
# client.set_starting_zone('left')
# client.run_challenge(123)
# time.sleep(0.2)
# print(client.get_challenge_solution())
# time.sleep(1)
# client.run_challenge(123)
# print(client.get_challenge_solution())
