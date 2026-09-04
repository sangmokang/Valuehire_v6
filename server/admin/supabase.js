"use strict";

const { AdminError } = require("./errors");

async function supabaseRaw(config, path, options = {}, apiKey = config.serviceRoleKey, bearer = apiKey) {
  let response;
  try {
    response = await fetch(`${config.supabaseUrl}${path}`, {
      ...options,
      headers: {
        apikey: apiKey,
        authorization: `Bearer ${bearer}`,
        "content-type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "Supabase request failed");
  }
  const text = await response.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch (error) {
      body = text;
    }
  }
  return { response, body };
}

async function supabaseFetch(config, path, options = {}, apiKey = config.serviceRoleKey, bearer = apiKey) {
  const result = await supabaseRaw(config, path, options, apiKey, bearer);
  if (!result.response.ok) {
    throw new AdminError("DEPENDENCY_UNAVAILABLE", result.response.status >= 500 ? 503 : 502, "Supabase request failed");
  }
  return result;
}

function encodeQuery(value) {
  return encodeURIComponent(value).replaceAll(".", "%2E");
}

module.exports = { encodeQuery, supabaseFetch, supabaseRaw };
