class TeamMember {
  final int id;
  final String name;
  final String phoneNumber;
  final String position;

  TeamMember({
    required this.id,
    required this.name,
    required this.phoneNumber,
    required this.position,
  });

  factory TeamMember.fromJson(Map<String, dynamic> json) {
    return TeamMember(
      id: json['id'],
      name: json['name'] ?? '',
      phoneNumber: json['phone_number'] ?? '',
      position: json['position'] ?? '',
    );
  }
}
