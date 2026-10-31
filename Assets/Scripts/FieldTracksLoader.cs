using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

/// <summary>
/// Python 파이프라인이 만든 경기장 좌표 CSV(frame,id,team,X,Y)를 읽는다.
/// X: 경기장 길이 방향(야드), Y: 먼 쪽 사이드라인에서의 거리(야드)
/// </summary>
public static class FieldTracksLoader
{
    public struct Sample
    {
        public int id;
        public string team;
        public Vector2 pos;   // (X, Y) in yards
    }

    public static Dictionary<int, List<Sample>> Load(string csvPath, out int maxFrame)
    {
        var data = new Dictionary<int, List<Sample>>();
        maxFrame = 0;
        if (!File.Exists(csvPath))
        {
            Debug.LogError("CSV file not found: " + csvPath);
            return data;
        }

        var lines = File.ReadAllLines(csvPath);
        var header = new List<string>(lines[0].Trim().Split(','));
        int iF = header.IndexOf("frame"), iId = header.IndexOf("id"), iT = header.IndexOf("team");
        int iX = header.IndexOf("X"), iY = header.IndexOf("Y");

        for (int n = 1; n < lines.Length; n++)
        {
            if (string.IsNullOrWhiteSpace(lines[n])) continue;
            var p = lines[n].Split(',');
            int frame = int.Parse(p[iF]);
            var s = new Sample
            {
                id = int.Parse(p[iId]),
                team = p[iT],
                pos = new Vector2(float.Parse(p[iX], CultureInfo.InvariantCulture),
                                  float.Parse(p[iY], CultureInfo.InvariantCulture))
            };
            if (!data.ContainsKey(frame)) data[frame] = new List<Sample>();
            data[frame].Add(s);
            if (frame > maxFrame) maxFrame = frame;
        }
        return data;
    }
}
