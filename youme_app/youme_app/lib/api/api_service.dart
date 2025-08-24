import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/item_location.dart';
import '../models/team_member.dart';
import '../models/usage_history.dart';

final String baseUrl = 'http://192.168.50.96:5000/api';

class ApiService {
  Future<List<ItemLocation>> fetchItemLocations() async {
    final response = await http.get(Uri.parse('$baseUrl/item_locations'));
    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((item) => ItemLocation.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load item locations. Status code: ${response.statusCode}');
    }
  }

  Future<List<TeamMember>> fetchTeamMembers() async {
    final response = await http.get(Uri.parse('$baseUrl/team_members'));
    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((item) => TeamMember.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load team members. Status code: ${response.statusCode}');
    }
  }

  Future<List<UsageHistory>> fetchUsageHistories() async {
    final response = await http.get(Uri.parse('$baseUrl/usage_histories'));

    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((item) => UsageHistory.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load usage histories. Status code: ${response.statusCode}');
    }
  }
}
