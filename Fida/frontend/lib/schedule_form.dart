import 'package:fida_ui/schedule_field.dart';
import 'package:flutter/material.dart';

class ScheduleForm extends StatefulWidget {
  final Map<dynamic, dynamic> daysData;

  const ScheduleForm({
    super.key,
    required this.daysData,
  });

  @override
  State<ScheduleForm> createState() => _ScheduleFormState();
}

class _ScheduleFormState extends State<ScheduleForm> {
  late final Map<dynamic, dynamic> daysData;

  @override
  void initState() {
    super.initState();
    daysData = widget.daysData;
  }

  void updateDayValue(String day, String value) {
    setState(() {
      daysData[day] =
          int.parse(value.substring(0, 2)) + int.parse(value.substring(3)) / 60;
    });
  }

  Map<dynamic, dynamic> getUpdatedDaysData() {
    return daysData;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        child: Column(
          children: daysData.keys.map((day) {
            return Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Padding(
                  padding: const EdgeInsets.only(bottom: 5),
                  child: Center(
                    child: Text(
                      day,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ),
                ScheduleField(
                  hourValue: (daysData[day] ~/ 60).toString(),
                  minuteValue: (daysData[day] % 60).toString(),
                  onChanged: (newValue) {
                    updateDayValue(day, newValue);
                  },
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}
