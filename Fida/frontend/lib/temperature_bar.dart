import 'package:fida_ui/riverpod.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TemperatureBar extends ConsumerWidget {
  final String ip;

  const TemperatureBar({
    super.key,
    required this.ip,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(getDataFuture);
    final currentValue = (data['fidaData'][ip]?['NTC1 TEMPINT']?['value'] ?? 0) / 10.0;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                0.0.toStringAsFixed(1),
                style: const TextStyle(
                  fontSize: 16,
                  color: Color.fromRGBO(45, 51, 83, 1.0),
                ),
              ),
              const SizedBox(width: 10),
              Stack(
                children: [
                  Container(
                    height: 26,
                    width: 130,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Colors.yellow, Colors.red],
                        stops: [0.0, 1.0],
                      ),
                      borderRadius: BorderRadius.circular(5),
                    ),
                  ),
                  Positioned(
                    left: (currentValue / 70) * 100.0,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 30,
                      height: 30,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: (currentValue >= 30 && currentValue <= 55)
                            ? const Color.fromRGBO(45, 51, 83, 1.0)
                            : Colors.red,
                      ),
                      child: Center(
                        child: Text(
                          currentValue.toStringAsFixed(1),
                          style: const TextStyle(
                              fontSize: 12, color: Color(0xFFD1E8FF)),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 10),
              Text(
                70.0.toStringAsFixed(1),
                style: const TextStyle(
                  fontSize: 16,
                  color: Color.fromRGBO(45, 51, 83, 1.0),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
