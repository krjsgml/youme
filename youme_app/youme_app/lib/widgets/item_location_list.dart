import 'package:flutter/material.dart';
import 'package:youme_app/models/item_location.dart';

class ItemLocationList extends StatelessWidget {
  final List<ItemLocation> itemLocations;

  ItemLocationList({required this.itemLocations});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: itemLocations.length,
      itemBuilder: (context, index) {
        final item = itemLocations[index];
        return ListTile(
          title: Text(item.name),
          subtitle: Text("Location: ${item.location}\nQuantity: ${item.quantity}"),
        );
      },
    );
  }
}
