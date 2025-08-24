class ItemLocation {
  final int id;
  final String location;
  final String name;
  final int quantity;

  ItemLocation({
    required this.id,
    required this.location,
    required this.name,
    required this.quantity,
  });

  factory ItemLocation.fromJson(Map<String, dynamic> json) {
    return ItemLocation(
      id: json['id'],
      location: json['location'] ?? '',
      name: json['name'] ?? '',
      quantity: json['quantity'] ?? 1,
    );
  }
}
