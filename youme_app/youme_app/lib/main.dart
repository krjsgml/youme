import 'package:flutter/material.dart';
import 'screens/members_screen.dart';
import 'screens/usage_screen.dart';
import 'screens/item_location_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YOUME App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => HomeScreen(),
        '/members': (context) => MembersScreen(),
        '/usage': (context) => UsageScreen(),
        '/item_location': (context) => ItemLocationScreen(),
      },
    );
  }
}

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('YOUME App'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(context, '/members');
              },
              child: Text('Manage Team Members'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(context, '/usage');
              },
              child: Text('Usage History'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pushNamed(context, '/item_location');
              },
              child: Text('Item Location'),
            ),
          ],
        ),
      ),
    );
  }
}
