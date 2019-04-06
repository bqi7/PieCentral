import msgpackrpc


class RuntimeClient:
    def __init__(self, host, port):
        self.host, self.port, self.client = host, port, None

    def connect(self):
        self.client = msgpackrpc.Client(msgpackrpc.Address(self.host, self.port))

    def disconnect(self):
        self.client.close()
        self.client = None

    def set_mode(self, mode=True):
        self.client.call('set_mode', mode)

    def set_alliance(self, alliance):
        self.client.call('set_alliance', alliance)

    def set_master(self, master):
        self.client.call('set_master', master)

    def set_starting_zone(self, zone):
        self.client.call('set_starting_zone', zone)

    def run_challenge(self, seed, timeout=1):
        self.client.notify('run_challenge', seed, timeout)

    def get_challenge_solution(self):
        return self.client.call('get_challenge_solution')


class RuntimeClientManager:
    def __init__(self, blue_alliance, gold_alliance):
        self.blue_alliance, self.gold_alliance = blue_alliance, gold_alliance
        self.clients = {
            team: RuntimeClient(f'192.168.128.{200 + team}', 6020)
            for team in self.blue_alliance + self.gold_alliance
        }
        for team in self.blue_alliance:
            self.clients[team].set_alliance('blue')
        for team in self.gold_alliance:
            self.clients[team].set_alliance('gold')

    def set_starting_zones(self, zones):
        for team, zone in zip(self.blue_alliance + self.gold_alliance, zones):
            self.clients[team].set_starting_zone(zone)

    def set_mode(self, mode):
        for client in self.clients.values():
            client.set_mode(mode)

    def get_challenge_solutions(self):
        return {team: client.get_challenge_solution() for team, client in self.clients.items()}

    def set_master_robots(self, blue_team, gold_team):
        self.clients[blue_team].set_master()
        self.clients[gold_team].set_master()
