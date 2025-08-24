import 'package:flutter/material.dart';
import 'package:youme_app/models/usage_history.dart';
import 'package:intl/intl.dart';

class UsageList extends StatelessWidget {
  final List<UsageHistory> usageHistory;
  final DateFormat datetimeFormat = DateFormat('yyyy-MM-dd HH:mm');
  final DateFormat dateFormat = DateFormat('yyyy-MM-dd');

  UsageList({required this.usageHistory});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: usageHistory.length,
      itemBuilder: (context, index) {
        final usage = usageHistory[index];

        String startTimeStr = usage.startTime != null ? datetimeFormat.format(usage.startTime!) : 'N/A';
        String stopTimeStr = usage.stopTime != null ? datetimeFormat.format(usage.stopTime!) : 'N/A';
        String usageDateStr = usage.usageDate != null ? dateFormat.format(usage.usageDate!) : 'N/A';

        return ListTile(
          title: Text("Usage #${usage.usageNum}"),
          subtitle: Text(
            "Name: ${usage.name}\n"
            "Start: $startTimeStr\n"
            "End: $stopTimeStr\n"
            "Date: $usageDateStr",
          ),
        );
      },
    );
  }
}
