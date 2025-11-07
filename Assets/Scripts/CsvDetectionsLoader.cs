using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

public class CsvDetectionsLoader
{
    public static Dictionary<int, List<Vector2>> LoadDetections(string csvPath)
    {
        var data = new Dictionary<int, List<Vector2>>();

        if (!File.Exists(csvPath))
        {
            Debug.LogError("CSV file not found: " + csvPath);
            return data;
        }

        using (var reader = new StreamReader(csvPath))
        {
            string header = reader.ReadLine(); // skip header
            while (!reader.EndOfStream)
            {
                string line = reader.ReadLine();
                if (string.IsNullOrWhiteSpace(line)) continue;

                string[] parts = line.Split(',');
                if (parts.Length < 6) continue;

                int frame = int.Parse(parts[0]);
                float x1 = float.Parse(parts[1], CultureInfo.InvariantCulture);
                float y1 = float.Parse(parts[2], CultureInfo.InvariantCulture);
                float x2 = float.Parse(parts[3], CultureInfo.InvariantCulture);
                float y2 = float.Parse(parts[4], CultureInfo.InvariantCulture);

                float cx = (x1 + x2) / 2f;
                float cy = (y1 + y2) / 2f;

                if (!data.ContainsKey(frame))
                    data[frame] = new List<Vector2>();

                data[frame].Add(new Vector2(cx, cy));
            }
        }

        return data;
    }
}
