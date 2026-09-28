from mininet.topo import Topo
from mininet.node import OVSKernelSwitch


class Topology(Topo):
    def build(self, N):

        routers = []

        gateway = "200.0.1.1"
        link_subnet_1 = {"bw": 100, "delay": "2ms"}
        router_1 = self.addSwitch("r_1", cls=OVSKernelSwitch, protocols="OpenFlow13")
        routers.append(router_1)
        for i in range(1, 4):
            proxy = self.addHost(
                f"p_1_{i}", ip=f"200.0.1.{i+1}/24", defaultRoute=f"via {gateway}"
            )
            host = self.addHost(
                f"h_1_{i}", ip=f"200.0.1.{i+4}/24", defaultRoute=f"via {gateway}"
            )
            self.addLink(host, router_1, **link_subnet_1)
            self.addLink(proxy, router_1, **link_subnet_1)

        link_subnets = {"bw": 1000, "delay": "10ms"}
        for i in range(2, N):
            gateway = f"200.{i}.0.1"
            router = self.addSwitch(
                f"r_{i}", cls=OVSKernelSwitch, protocols="OpenFlow13"
            )
            routers.append(router)
            for j in range(1, 4):
                proxy = self.addHost(
                    f"p_{i}_{j}",
                    ip=f"200.{i}.0.{j+1}/29",
                    defaultRoute=f"via {gateway}",
                )
                self.addLink(proxy, router, **link_subnets)

        gateway = f"200.{N}.2.1"
        link_subnet_n = {"bw": 100, "delay": "2ms"}
        router_n = self.addSwitch(f"r_{N}", cls=OVSKernelSwitch, protocols="OpenFlow13")
        routers.append(router_n)
        s_1 = self.addHost(f"s1", ip=f"200.{N}.2.5/24", defaultRoute=f"via {gateway}")
        for i in range(1, 4):
            proxy = self.addHost(
                f"p_{N}_{i}", ip=f"200.{N}.2.{i+1}/24", defaultRoute=f"via {gateway}"
            )
            self.addLink(proxy, router_n, **link_subnet_n)
        self.addLink(s_1, router_n, **link_subnet_1)

        link_routers = {"bw": 1000, "delay": "10ms"}
        for i in range(len(routers) - 1):
            self.addLink(routers[i], routers[i + 1], **link_routers)
