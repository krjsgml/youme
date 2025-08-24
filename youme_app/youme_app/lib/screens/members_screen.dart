import 'package:flutter/material.dart';
import 'package:youme_app/api/api_service.dart';
import 'package:youme_app/models/team_member.dart';
import 'package:youme_app/widgets/member_list.dart';

class MembersScreen extends StatefulWidget {
  @override
  _MembersScreenState createState() => _MembersScreenState();
}

class _MembersScreenState extends State<MembersScreen> {
  late Future<List<TeamMember>> members;

  @override
  void initState() {
    super.initState();
    members = ApiService().fetchTeamMembers();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Team Members"),
      ),
      body: FutureBuilder<List<TeamMember>>(
        future: members,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return Center(child: Text("No members found"));
          } else {
            return MemberList(members: snapshot.data!);
          }
        },
      ),
    );
  }
}
