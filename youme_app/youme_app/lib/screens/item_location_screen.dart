import 'package:flutter/material.dart';
import 'package:youme_app/api/api_service.dart';
import 'package:youme_app/models/item_location.dart';

class ItemLocationScreen extends StatefulWidget {
  @override
  _ItemLocationScreenState createState() => _ItemLocationScreenState();
}

class _ItemLocationScreenState extends State<ItemLocationScreen> {
  late Future<List<ItemLocation>> futureItemLocations;

  @override
  void initState() {
    super.initState();
    futureItemLocations = ApiService().fetchItemLocations(); // API 호출
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Item Location"),
      ),
      body: FutureBuilder<List<ItemLocation>>(
        future: futureItemLocations,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (snapshot.hasData) {
            List<ItemLocation> itemLocations = snapshot.data!;
            return ListView.builder(
              itemCount: itemLocations.length,
              itemBuilder: (context, index) {
                return ListTile(
                  title: Text(itemLocations[index].name),
                  subtitle: Text("Location: ${itemLocations[index].location}, Quantity: ${itemLocations[index].quantity}"),
                );
              },
            );
          } else {
            return Center(child: Text("No data available"));
          }
        },
      ),
    );
  }
}
