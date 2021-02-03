using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights.Extensibility;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Logging;
using Npgsql;
using Npgsql.TypeHandlers;
using PackageUrl;

namespace MetricAPI
{
    public class MainAPIEndpoint
    {
        //private Microsoft.ApplicationInsights.TelemetryClient TelemetryClient;
        private static readonly NpgsqlConnection? DatabaseConnection;

        static MainAPIEndpoint()
        {

            var connString = Environment.GetEnvironmentVariable("DATABASE_CONNECTION_STRING");
            if (connString == null)
            {
                throw new ArgumentNullException("Unable to find DATABASE_CONNECTION_STRING environment variable.");
            }

            if (DatabaseConnection == null)
            {
                DatabaseConnection = new NpgsqlConnection(connString);
                DatabaseConnection.Open();
            }
        }

        public MainAPIEndpoint()
        {
            //TelemetryClient = new Microsoft.ApplicationInsights.TelemetryClient(telemetryConfiguration);
        }

        private static IActionResult JsonError(string message)
        {
            var content = new Dictionary<string, string>()
            {
                { "status", "error" },
                { "message", message }
            };
            var result = new JsonResult(content)
            {
                StatusCode = 400
            };
            return result;
        }

        private static IActionResult JsonSuccess(string? message, object? data)
        {
            var content = new Dictionary<string, object>()
            {
                { "status", "success" },
                { "message", message ?? "OK" }
            };

            if (data != null)
            {
                content["data"] = data;
            }

            var result = new JsonResult(content)
            {
                StatusCode = 200
            };
            return result;
        }

        private async Task<int> DoClearMetrics(string metricKey, PackageURL packageUrl, NpgsqlTransaction? transaction)
        {
            using var sqlCommand = new NpgsqlCommand
            {
                Connection = DatabaseConnection
            };

            if (transaction != null)
            {
                sqlCommand.Transaction = transaction;
            }

            sqlCommand.CommandText = "DELETE FROM metrics WHERE package_url=@package_url AND key=@key";
            sqlCommand.Parameters.AddWithValue("@package_url", packageUrl.ToString());
            sqlCommand.Parameters.AddWithValue("@key", metricKey);

            return await sqlCommand.ExecuteNonQueryAsync();
        }

        [FunctionName("AddMetric")]
        public async Task<IActionResult> AddMetric(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = null)] HttpRequest req, ILogger log)
        {
            var root = (await JsonDocument.ParseAsync(req.Body)).RootElement;
            var errorList = new List<string>();
            var currentIndex = -1;
            var totalChanges = 0;
            if (DatabaseConnection == null)
            {
                log.LogError("No database connection initialized.");
                return JsonError("Database failed to initialize.");
            }

            var transaction = await DatabaseConnection.BeginTransactionAsync();

            try
            {
                foreach (var package in root.EnumerateArray())
                {
                    ++currentIndex;

                    if (!package.TryGetProperty("package_url", out JsonElement packageUrlElt) ||
                        !package.TryGetProperty("key", out JsonElement keyElt) ||
                        !package.TryGetProperty("operation", out JsonElement operationElt))
                    {
                        errorList.Add($"Missing required field (index #{currentIndex})");
                        continue;
                    }
                    var packageUrl = new PackageURL(packageUrlElt.GetString());
                    var key = keyElt.GetString();

                    var operation = operationElt.GetString();
                    if (operation != "insert" && operation != "replace")
                    {
                        errorList.Add($"Invalid operation specified (index #{currentIndex})");
                        continue;
                    }

                    if (!package.TryGetProperty("values", out JsonElement valuesElt))
                    {
                        errorList.Add($"No values specified (index #{currentIndex})");
                        continue;
                    }

                    if (operation == "replace")
                    {
                        totalChanges += await DoClearMetrics(key, packageUrl, transaction);
                    }

                    foreach (var item in valuesElt.EnumerateArray())
                    {
                        var timestamp = DateTime.Now;
                        if (item.TryGetProperty("timestamp", out JsonElement timestampElement))
                        {
                            timestampElement.TryGetDateTime(out timestamp);
                        };
                        if (!item.TryGetProperty("value", out JsonElement valueElt))
                        {
                            continue;
                        }
                        JsonElement? properties = null;
                        if (item.TryGetProperty("properties", out JsonElement propertiesElt))
                        {
                            properties = (JsonElement?)propertiesElt;
                        }

                        var value = valueElt.ToString();
                        try
                        {
                            totalChanges += await InsertMetricAsync(packageUrl, key, value, timestamp, properties, log, transaction);
                        }
                        catch (Exception ex)
                        {
                            errorList.Add($"Error inserting into {key}: {ex.Message}");
                        }

                    }
                }
                
            } 
            catch(Exception ex)
            {
                errorList.Add($"Error processing payload, rolling back: {ex.Message}");
                transaction.Rollback();
            }

            try
            {
                log.LogInformation("Committing transaction.");
                transaction.Commit();
            }
            catch (Exception)
            {
                // ignore OK
            }

            if (errorList.Any())
            {
                return JsonError(string.Join(";", errorList));
            }
            else
            {
                return JsonSuccess($"Updated {totalChanges} records.", null);
            }
        }

        private static async Task<int> InsertMetricAsync(PackageURL packageUrl, string key, string value, DateTime timestamp, JsonElement? properties, ILogger log, NpgsqlTransaction transaction)
        {
            await using var cmdIns = new NpgsqlCommand("INSERT INTO metrics (package_url, key, properties, value, timestamp) VALUES (@package_url, @key, @properties, @value, @timestamp)", transaction.Connection, transaction);
            cmdIns.Parameters.AddWithValue("@package_url", packageUrl.ToString());
            cmdIns.Parameters.AddWithValue("@key", key);
            if (properties.HasValue)
            {
                cmdIns.Parameters.Add(new NpgsqlParameter("@properties", NpgsqlTypes.NpgsqlDbType.Jsonb) { Value = properties });
            }
            else
            {
                cmdIns.Parameters.AddWithValue("@properties", DBNull.Value);
            }
            cmdIns.Parameters.AddWithValue("@value", value);
            cmdIns.Parameters.AddWithValue("@timestamp", timestamp);
            return await cmdIns.ExecuteNonQueryAsync();
        }
    }
}