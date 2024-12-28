import multiprocessing as mp
from pysnmp.hlapi import *


class SNMPFunctions:

    @staticmethod
    def snmp_get(oids, target, community, values):
        result = {}
        for oid in oids:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=0),
                UdpTransportTarget((target, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            error_indication, error_status, error_index, var_binds = next(iterator)

            print(var_binds)

            if error_indication:
                result[oid] = 'N/A'
            elif error_status:
                result[oid] = 'N/A'
            else:
                for varBind in var_binds:
                    result[oid] = varBind[1]

        values[target] = result

    def get_value_on_multiple_ips(self, oids, ip_list, community, values):
        processes = []
        for ip in ip_list:
            try:
                process = mp.Process(target=self.snmp_get, args=(oids, ip, community, values))
                processes.append(process)
                process.start()
            except Exception as e:
                raise Exception(e.args[0])
        for process in processes:
            try:
                process.join()
            except Exception as e:
                raise Exception(f'(function: get_value_on_multiple_ips): Error while joining processes: {e}')

    @staticmethod
    def set_value_on_ip(ip, oid, community, value):
        if isinstance(value, int) or isinstance(value, str):
            value = Integer(value)

        error_indication, error_status, error_index, var_binds = next(
            setCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=0),
                UdpTransportTarget((ip, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid), value)
            )
        )

        if error_indication:
            raise Exception(f"SNMP error on set ip value : {error_indication}")

    def set_value_on_multiple_ips(self, oid, ip_list, community, value):
        for ip in ip_list:
            try:
                self.set_value_on_ip(ip, oid, community, value)
            except Exception as e:
                raise Exception(e.args[0])
