import 'package:flutter/material.dart';

class ScheduleField extends StatefulWidget {
  final String hourValue;
  final String minuteValue;
  final ValueChanged<String> onChanged;

  const ScheduleField({
    super.key,
    required this.hourValue,
    required this.minuteValue,
    required this.onChanged,
  });

  @override
  State<ScheduleField> createState() => _ScheduleFieldState();
}

class _ScheduleFieldState extends State<ScheduleField> {
  final myController = TextEditingController();

  @override
  void initState() {
    final finalHour = ((widget.hourValue.length == 2)
        ? widget.hourValue
        : '0${widget.hourValue}');
    final finalMinute = ((widget.minuteValue.length == 2)
        ? widget.minuteValue
        : '0${widget.minuteValue}');
    super.initState();
    myController.text = '$finalHour:$finalMinute';
    myController.addListener(() {
      widget.onChanged(myController.text);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: SizedBox(
        height: 35,
        width: 70,
        child: Center(
          child: TextField(
            controller: myController,
            maxLength: 5,
            cursorColor: Colors.black,
            style: const TextStyle(fontSize: 14),
            textAlign: TextAlign.center,
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(20),
                borderSide: const BorderSide(color: Colors.green),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(20),
                borderSide: const BorderSide(color: Colors.green),
              ),
              counterText: '',
            ),
          ),
        ),
      ),
    );
  }
}
