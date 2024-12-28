import 'package:fida_ui/riverpod.dart';
import 'package:fida_ui/schedule_form.dart';
import 'package:fida_ui/temperature_bar.dart';
import 'package:fida_ui/api_futures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:async';

class DataCard extends ConsumerStatefulWidget {
  const DataCard({
    super.key,
    required this.borderColor,
    required this.iconName,
    required this.ip,
    required this.state,
  });

  final Color borderColor;
  final IconData iconName;
  final String ip;
  final String state;

  @override
  _DataCardState createState() => _DataCardState();
}

class _DataCardState extends ConsumerState<DataCard> {
  late Timer _timer;
  late var data;

  @override
  void initState() {
    super.initState();
    _checkForUpdates();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    data = ref.watch(getDataFuture);
  }

  void _checkForUpdates() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      final newData = await ref.watch(getDataFuture);
      if (newData != null && newData is Map<String, dynamic>) {
        setState(() {
          data = newData;
        });
      }
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final List fidaData = ['LUX1', 'FAN1', 'FAN2', 'FAN1 PWM', 'FAN2 PWM'];
    final fidaIcons = {
      'LUX1': {
        'name': Icons.settings_brightness_outlined,
        'color': Colors.black38,
        'size': 25.0
      },
      'FAN1': {
        'name': FontAwesomeIcons.fan,
        'color': Colors.black38,
        'size': 22.0
      },
      'FAN2': {
        'name': FontAwesomeIcons.fan,
        'color': Colors.black38,
        'size': 22.0
      },
      'FAN1 PWM': {
        'name': Icons.electric_bolt,
        'color': Colors.yellow,
        'size': 25.0
      },
      'FAN2 PWM': {
        'name': Icons.electric_bolt,
        'color': Colors.yellow,
        'size': 25.0
      },
    };
    final Map<String, dynamic> daysData = {};
    final Map<String, dynamic> daysDataCopy = {};
    final List<String> daysKeys = [
      'Sun_ON',
      'Sun_OFF',
      'Mon_ON',
      'Mon_OFF',
      'Tue_ON',
      'Tue_OFF',
      'Wed_ON',
      'Wed_OFF',
      'Thu_ON',
      'Thu_OFF',
      'Fri_ON',
      'Fri_OFF',
      'Sat_ON',
      'Sat_OFF'
    ];

    for (var key in daysKeys) {
      if (data['fidaData'][widget.ip].containsKey(key)) {
        daysData[key] = data['fidaData'][widget.ip][key]?['value'] ?? 0;
        daysDataCopy[key] = data['fidaData'][widget.ip][key]?['value'] ?? 0;
      }
    }

    return GestureDetector(
      child: Padding(
        padding: const EdgeInsets.all(5),
        child: SizedBox(
          height: 330,
          width: 230,
          child: Card(
            color: Colors.white,
            elevation: 5,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: BorderSide(color: widget.borderColor, width: 2),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        widget.state == "UP" &&
                                data['error'] !=
                                    "IP status is not ON or no result found"
                            ? widget.iconName
                            : Icons.cancel_presentation_rounded,
                        color: widget.borderColor,
                        size: 60,
                      ),
                      Text(
                        widget.ip,
                        style: TextStyle(
                          color: widget.borderColor,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        widget.state,
                        style: TextStyle(
                          color: widget.borderColor,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                if (widget.state == "UP" &&
                    data['fidaData'][widget.ip]['error'] == null) ...[
                  Column(
                    children: fidaData
                        .map((elem) => RichText(
                              text: TextSpan(
                                children: [
                                  WidgetSpan(
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(
                                          vertical: 1),
                                      child: Icon(
                                        fidaIcons[elem]?['name'] as IconData?,
                                        size:
                                            fidaIcons[elem]?['size'] as double?,
                                        color:
                                            fidaIcons[elem]?['color'] as Color?,
                                      ),
                                    ),
                                  ),
                                  const WidgetSpan(
                                    child: SizedBox(width: 4),
                                  ),
                                  WidgetSpan(
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(
                                          vertical: 4.0),
                                      child: Text(
                                        '$elem: ',
                                        style: const TextStyle(
                                          color: Colors.black,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const WidgetSpan(
                                    child: SizedBox(width: 4),
                                  ),
                                  WidgetSpan(
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(
                                          vertical: 4.0),
                                      child: Text(
                                        data['fidaData']?[widget.ip]?[elem]
                                                    ?['value']
                                                ?.toString() ??
                                            'N/A',
                                        style: const TextStyle(
                                          color: Colors.black,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ))
                        .toList(),
                  ),
                  Column(children: [
                    const Padding(
                      padding: EdgeInsets.only(bottom: 5),
                      child: Center(
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.thermostat_outlined,
                                color: Colors.orange, size: 25),
                            SizedBox(width: 4),
                            Text('Monitor Temperature',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Color.fromRGBO(45, 51, 83, 1.0),
                                  fontWeight: FontWeight.bold,
                                ))
                          ],
                        ),
                      ),
                    ),
                    TemperatureBar(
                      ip: widget.ip,
                    ),
                  ])
                ] else if (widget.state == "UP") ...[
                  const Center(
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        FaIcon(FontAwesomeIcons.fileInvoice, color: Colors.red),
                        SizedBox(width: 2),
                        Text(
                          'Error: No data found',
                          style: TextStyle(
                            color: Colors.red,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ]
              ],
            ),
          ),
        ),
      ),
      onTap: () {
        if (widget.state == "UP" &&
            data['fidaData'][widget.ip]['error'] == null) {
          showDialog(
            context: context,
            builder: (BuildContext context) {
              return AlertDialog(
                backgroundColor: Colors.white,
                title: const Text(
                  'Set Schedule',
                  style: TextStyle(
                      color: Color.fromRGBO(45, 51, 83, 1.0),
                      fontSize: 22,
                      fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                content: SizedBox(
                    height: 300,
                    width: 150,
                    child: ScheduleForm(daysData: daysData)),
                actions: <Widget>[
                  Center(
                    child: TextButton(
                      style:
                          TextButton.styleFrom(backgroundColor: Colors.green),
                      child: const Text(
                        'Add',
                        style: TextStyle(fontSize: 18, color: Colors.white),
                      ),
                      onPressed: () async {
                        final Map<dynamic, dynamic> updatedDaysData = {};

                        daysData.forEach((key, value) {
                          if (value != daysDataCopy[key]) {
                            updatedDaysData[key] = value;
                          }
                        });

                        await updateScheduleApi(
                            context, widget.ip, updatedDaysData);

                        // Refresh data
                        ref.read(getDataFuture.notifier).getData();

                        Navigator.of(context).pop();
                      },
                    ),
                  ),
                ],
              );
            },
          );
        }
      },
    );
  }
}
