#!/usr/bin/env bash
# Deploy dist/ to AWS: private S3 bucket behind CloudFront, HTTPS via ACM.
#
# First run creates the bucket, certificate and distribution and prints the DNS
# records to add at Namecheap. Re-running after DNS is in place just syncs files
# and invalidates the cache.
#
#   DOMAIN=k12boss.com ./tools/deploy.sh
set -euo pipefail

DOMAIN="${DOMAIN:-k12boss.com}"
BUCKET="${BUCKET:-${DOMAIN}-site}"
REGION="${REGION:-us-east-1}"   # ACM certs for CloudFront must live in us-east-1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$ROOT/.deploy-state"
mkdir -p "$STATE"

python3 "$ROOT/tools/build.py"

# 1. Bucket (private; CloudFront reads it through an origin access control)
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
fi

# 2. Upload: HTML revalidates every time, assets cache for a day
aws s3 sync "$ROOT/dist" "s3://$BUCKET" --delete --exclude "index.html" \
  --cache-control "public, max-age=86400"
aws s3 cp "$ROOT/dist/index.html" "s3://$BUCKET/index.html" \
  --cache-control "public, max-age=0, must-revalidate" --content-type "text/html; charset=utf-8"

# 3. Certificate for apex + www
if [[ ! -s "$STATE/cert_arn" ]]; then
  aws acm request-certificate --region us-east-1 --domain-name "$DOMAIN" \
    --subject-alternative-names "www.$DOMAIN" --validation-method DNS \
    --query CertificateArn --output text > "$STATE/cert_arn"
  sleep 10
fi
CERT_ARN="$(cat "$STATE/cert_arn")"
CERT_STATUS="$(aws acm describe-certificate --region us-east-1 --certificate-arn "$CERT_ARN" --query Certificate.Status --output text)"
if [[ "$CERT_STATUS" != "ISSUED" ]]; then
  echo
  echo "Certificate is $CERT_STATUS. Add these CNAME records at Namecheap (Advanced DNS), then re-run:"
  aws acm describe-certificate --region us-east-1 --certificate-arn "$CERT_ARN" \
    --query 'Certificate.DomainValidationOptions[].ResourceRecord.[Name,Value]' --output text \
    | sort -u | while read -r name value; do
        echo "  CNAME  host: ${name%.$DOMAIN.}  value: $value"
      done
  exit 0
fi

# 4. CloudFront distribution
if [[ ! -s "$STATE/dist_id" ]]; then
  OAC_ID="$(aws cloudfront create-origin-access-control --origin-access-control-config \
    "Name=${BUCKET}-oac,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" \
    --query OriginAccessControl.Id --output text)"
  cat > "$STATE/dist.json" <<JSON
{
  "CallerReference": "k12boss-$(date +%s)",
  "Aliases": {"Quantity": 2, "Items": ["$DOMAIN", "www.$DOMAIN"]},
  "DefaultRootObject": "index.html",
  "Origins": {"Quantity": 1, "Items": [{
    "Id": "s3", "DomainName": "$BUCKET.s3.$REGION.amazonaws.com",
    "OriginAccessControlId": "$OAC_ID",
    "S3OriginConfig": {"OriginAccessIdentity": ""}
  }]},
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3", "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "Compress": true,
    "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
  },
  "CustomErrorResponses": {"Quantity": 1, "Items": [{"ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 60}]},
  "ViewerCertificate": {"ACMCertificateArn": "$CERT_ARN", "SSLSupportMethod": "sni-only", "MinimumProtocolVersion": "TLSv1.2_2021"},
  "HttpVersion": "http2and3",
  "PriceClass": "PriceClass_100",
  "Enabled": true,
  "Comment": "K12 BOSS landing page"
}
JSON
  aws cloudfront create-distribution --distribution-config "file://$STATE/dist.json" \
    --query 'Distribution.[Id,ARN,DomainName]' --output text > "$STATE/dist_info"
  awk '{print $1}' "$STATE/dist_info" > "$STATE/dist_id"
  DIST_ARN="$(awk '{print $2}' "$STATE/dist_info")"
  cat > "$STATE/policy.json" <<JSON
{"Version": "2012-10-17", "Statement": [{
  "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"},
  "Action": "s3:GetObject", "Resource": "arn:aws:s3:::$BUCKET/*",
  "Condition": {"StringEquals": {"AWS:SourceArn": "$DIST_ARN"}}
}]}
JSON
  aws s3api put-bucket-policy --bucket "$BUCKET" --policy "file://$STATE/policy.json"
fi

DIST_ID="$(cat "$STATE/dist_id")"
CF_DOMAIN="$(aws cloudfront get-distribution --id "$DIST_ID" --query Distribution.DomainName --output text)"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" >/dev/null

# 5. DNS: point apex and www at CloudFront in Route 53 (if the zone is managed there)
if [[ -s "$STATE/zone_id" ]]; then
  ZONE_ID="$(cat "$STATE/zone_id")"
  python3 - "$DOMAIN" "$CF_DOMAIN" > "$STATE/alias.json" <<'PY'
import json, sys
domain, cf = sys.argv[1], sys.argv[2]
changes = []
for name in (domain, "www." + domain):
    for rtype in ("A", "AAAA"):
        changes.append({"Action": "UPSERT", "ResourceRecordSet": {
            "Name": name, "Type": rtype,
            # Z2FDTNDATAQYW2 is the fixed hosted zone ID for every CloudFront distribution
            "AliasTarget": {"HostedZoneId": "Z2FDTNDATAQYW2", "DNSName": cf, "EvaluateTargetHealth": False}}})
print(json.dumps({"Comment": "K12 BOSS site", "Changes": changes}))
PY
  aws route53 change-resource-record-sets --hosted-zone-id "$ZONE_ID" \
    --change-batch "file://$STATE/alias.json" --query ChangeInfo.Status --output text
  echo
  echo "Deployed. https://$DOMAIN and https://www.$DOMAIN point at https://$CF_DOMAIN"
else
  echo
  echo "Deployed. CloudFront: https://$CF_DOMAIN"
  echo "Add DNS records at your registrar:"
  echo "  ALIAS  host: @    value: $CF_DOMAIN"
  echo "  CNAME  host: www  value: $CF_DOMAIN"
fi
