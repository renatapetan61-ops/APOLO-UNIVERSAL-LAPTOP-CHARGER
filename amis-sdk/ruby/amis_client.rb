#!/usr/bin/env ruby
# frozen_string_literal: true
# Ruby client for the local APOLO AMIS host agent.
require "net/http"
require "json"
require "uri"
BASE = "http://127.0.0.1:8765"
def amis_request(path, method = :get)
  uri = URI("#{BASE}#{path}")
  request = method == :post ? Net::HTTP::Post.new(uri) : Net::HTTP::Get.new(uri)
  request["Cache-Control"] = "no-store"
  response = Net::HTTP.start(uri.host, uri.port, read_timeout: 35) { |http| http.request(request) }
  raise "Host agent HTTP #{response.code}: #{response.body}" unless response.is_a?(Net::HTTPSuccess)
  JSON.parse(response.body)
end
puts JSON.pretty_generate(discovery: amis_request("/v1/camera"), capture: amis_request("/v1/camera/capture", :post))
