import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fida_ui/riverpod.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:io';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter/material.dart';

void showNotification(BuildContext context, String message) {
  final snackBar = SnackBar(
    content: Text(message),
    backgroundColor:
        message.contains('successfully') ? Colors.green : Colors.red,
    behavior: SnackBarBehavior.floating,
    margin: EdgeInsets.only(top: 10, left: 10, right: 10),
  );
  ScaffoldMessenger.of(context).showSnackBar(snackBar);
}

final stateOfIpsProvider =
    StateNotifierProvider<StateOfIpsNotifier, Map<String, String>>((ref) {
  return StateOfIpsNotifier();
});

class StateOfIpsNotifier extends StateNotifier<Map<String, String>> {
  StateOfIpsNotifier() : super({});

  Future<void> assignStateOfApi(WidgetRef ref) async {
    final getDataFromApi = ref.read(getDataFuture.notifier);
    await getDataFromApi.getData();

    Map<String, String> newStateOfIps = {};

    if (getDataFromApi.state['ipsData'] != null &&
        getDataFromApi.state['ipsData'].isNotEmpty &&
        getDataFromApi.state['ipsData'][0] != null &&
        getDataFromApi.state['ipsData'][0].containsKey('ips')) {
      List<dynamic> ipsList = getDataFromApi.state['ipsData'][0]['ips'];

      for (var i = 0; i < ipsList.length; i++) {
        var x = ipsList[i];
        try {
          (checkSpecificIp(getDataFromApi.state['alarmsData'], x) ||
                  getDataFromApi.state['fidaData'][x]?["error"] ==
                      "IP status is not ON or no result found")
              ? newStateOfIps[x] = "DOWN"
              : newStateOfIps[x] = "UP";
        } catch (e) {
          print('Error processing IP $x: $e');
        }
      }
    } else {
      print('No IP data found');
    }
    // print('New state of IPs: $newStateOfIps');
    state = newStateOfIps;
  }
}

bool checkSpecificIp(Map<String, dynamic> alarmsData, String specificIp) {
  if (alarmsData == null || alarmsData["ip_broke_down"] == null) {
    return false;
  }
  List<dynamic> ipList = alarmsData["ip_broke_down"];
  bool ipFound = ipList.any((element) => element['ip'] == specificIp);
  return ipFound;
}

Future<void> updateScheduleApi(
    BuildContext context, String ip, Map<dynamic, dynamic> daysData) async {
  final String jsonString =
      await rootBundle.loadString('assets/configs/config.json');
  final data = jsonDecode(jsonString);
  final ip_port = data['ip'];
  final url = Uri.parse('http://$ip_port/schedule/$ip');

  try {
    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(daysData),
    );

    if (response.statusCode == 307) {
      final redirectUrl = response.headers['location'];
      if (redirectUrl != null) {
        final newResponse = await http.put(
          Uri.parse(redirectUrl),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(daysData),
        );
        if (newResponse.statusCode == 200) {
          showNotification(context, 'Schedule updated successfully');
        } else {
          showNotification(
              context, 'Failed to update schedule: ${newResponse.statusCode}');
        }
      } else {
        showNotification(context, 'Redirect URL not found');
      }
    } else if (response.statusCode == 200) {
      showNotification(context, 'Schedule updated successfully');
    } else {
      showNotification(
          context, 'Failed to update schedule: ${response.statusCode}');
    }
  } on SocketException catch (e) {
    showNotification(context, 'Network error: $e');
  } catch (e) {
    showNotification(context, 'Unexpected error: $e');
  }
}
