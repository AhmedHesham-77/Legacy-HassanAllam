import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';
import 'package:fida_ui/data_card.dart';
import 'package:fida_ui/api_futures.dart';
import 'package:fida_ui/riverpod.dart';
import 'package:fida_ui/restart_widget.dart'; // Import the RestartWidget

void main() {
  runApp(
    const ProviderScope(
      child: RestartWidget(
        child: MyApp(),
      ),
    ),
  );
}

class MyApp extends ConsumerStatefulWidget {
  const MyApp({super.key});

  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends ConsumerState<MyApp> {
  late Timer _timer;
  bool _serverAvailable = false;

  @override
  void initState() {
    super.initState();
    _checkServerAvailability();
    _updateStateOfIps();
  }

  void _refreshApp() {
    setState(() {});
  }

  void _checkServerAvailability() {
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      try {
        final data = ref.read(getDataFuture);
        if (data['error'] == null) {
          if (!_serverAvailable) {
            setState(() {
              _serverAvailable = true;
            });
            _refreshApp();
          }
        } else {
          if (_serverAvailable) {
            setState(() {
              _serverAvailable = false;
            });
            _refreshApp();
          }
        }
      } catch (e) {
        if (_serverAvailable) {
          setState(() {
            _serverAvailable = false;
          });
          _refreshApp();
        }
      }
    });
  }

  void _updateStateOfIps() async {
    await ref.read(stateOfIpsProvider.notifier).assignStateOfApi(ref);
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final stateOfIps = ref.watch(stateOfIpsProvider);
    final data = ref.watch(getDataFuture);

    return MaterialApp(
      scrollBehavior:
          const MaterialScrollBehavior().copyWith(scrollbars: false),
      home: !_serverAvailable
          ? const Scaffold(
              body: Center(child: Text("Server not available. Retrying...")),
            )
          : data.isEmpty
              ? const Scaffold(
                  body: Center(child: CircularProgressIndicator()),
                )
              : Scaffold(
                  appBar: PreferredSize(
                    preferredSize: const Size.fromHeight(120.0),
                    child: Container(
                      height: 110.0,
                      decoration: BoxDecoration(
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.5),
                            spreadRadius: 5,
                            blurRadius: 7,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: AppBar(
                        toolbarHeight: MediaQuery.of(context).size.height,
                        shadowColor: Colors.red,
                        shape: const RoundedRectangleBorder(
                          borderRadius: BorderRadius.vertical(
                            bottom: Radius.circular(30),
                          ),
                        ),
                        title: const Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                "Fida UI",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 35,
                                  fontWeight: FontWeight.bold,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                              Text(
                                "Control panel",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                            ],
                          ),
                        ),
                        backgroundColor: const Color.fromRGBO(45, 51, 83, 1.0),
                      ),
                    ),
                  ),
                  backgroundColor: const Color(0xFFD1E8FF),
                  body: Center(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.vertical,
                      child: Wrap(
                        spacing: 8.0,
                        runSpacing: 8.0,
                        children: stateOfIps.keys.map((ip) {
                          return Consumer(
                            builder: (context, ref, child) {
                              return DataCard(
                                borderColor: stateOfIps[ip] == "UP"
                                    ? Colors.green
                                    : Colors.red,
                                iconName: Icons.airplay_rounded,
                                ip: ip,
                                state: stateOfIps[ip].toString(),
                              );
                            },
                          );
                        }).toList(),
                      ),
                    ),
                  ),
                  floatingActionButton: FloatingActionButton(
                    onPressed: () => RestartWidget.restartApp(context),
                    backgroundColor: const Color.fromRGBO(45, 51, 83, 1.0),
                    child: const Icon(
                      Icons.refresh,
                      color: Colors.white,
                    ),
                  ),
                ),
    );
  }
}
