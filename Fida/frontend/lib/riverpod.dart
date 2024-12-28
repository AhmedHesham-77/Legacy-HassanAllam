import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

final getDataFuture =
    StateNotifierProvider<GetDataFromApi, Map<String, dynamic>>(
        (ref) => GetDataFromApi());

class GetDataFromApi extends StateNotifier<Map<String, dynamic>> {
  GetDataFromApi() : super({}) {
    getData();
    _startPeriodicUpdate();
  }

  final newState = <String, dynamic>{};

  Timer? _timer;

  Future<Map<String, dynamic>?> getData() async {
    final String jsonString =
        await rootBundle.loadString('assets/configs/config.json');
    final data = jsonDecode(jsonString);
    final ip_port = data['ip'];

    try {
      http.Response allIpsResponse =
          await http.get(Uri.parse('http://$ip_port/'));
      http.Response pingAlarms =
          await http.get(Uri.parse('http://$ip_port/ping-alarms'));
      http.Response ips = await http.get(Uri.parse('http://$ip_port/ips'));

      var fidaJson = jsonDecode(allIpsResponse.body);
      var alarmsJson = jsonDecode(pingAlarms.body);
      var ipsJson = jsonDecode(ips.body);

      newState['error'] = null;

      if (fidaJson is Map) {
        newState['fidaData'] = fidaJson.cast<String, dynamic>();
      }

      if (alarmsJson is Map) {
        newState['alarmsData'] = alarmsJson.cast<String, dynamic>();
      }

      if (ipsJson is List) {
        newState['ipsData'] = ipsJson;
      } else if (ipsJson is Map) {
        newState['ipsData'] = [ipsJson];
      }

      state = newState;
      return newState;
    } catch (e) {
      newState['error'] = e.toString();
      state = newState;
      return null;
    }
  }

  void _startPeriodicUpdate() {
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) {
      getData();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
