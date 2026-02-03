"""
Moltbook API Client - Centralized API access for all Moltbook operations
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


class MoltbookClient:
    """Centralized client for all Moltbook API operations"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("MOLTBOOK_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        self.timeout = 30
        self.cache = {}
        self.last_fetch_time = {}
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request with error handling"""
        url = f"{MOLTBOOK_BASE_URL}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json(), "status": 200}
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limited", "status": 429}
            elif response.status_code == 401:
                return {"success": False, "error": "Unauthorized", "status": 401}
            elif response.status_code == 500:
                return {"success": False, "error": "Server error", "status": 500}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "status": response.status_code}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout", "status": 0}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error", "status": 0}
        except Exception as e:
            return {"success": False, "error": str(e), "status": 0}
    
    # ==================== FEED OPERATIONS ====================
    
    def get_feed(self, limit: int = 50, sort: str = "new") -> list:
        """Get main feed posts - uses /posts endpoint like the poller"""
        result = self._request("GET", f"/posts?limit={limit}&sort={sort}")
        if result["success"]:
            return result["data"].get("posts", [])
        return []
    
    def get_community_feed(self, community: str, limit: int = 25) -> list:
        """Get posts from a specific community submolt (e.g., airesearch, tech, general)"""
        result = self._request("GET", f"/posts?submolt={community}&limit={limit}")
        if result["success"]:
            return result["data"].get("posts", [])
        return []
    
    def get_all_feeds(self, main_limit: int = 50, community_limit: int = 25) -> dict:
        """Get posts from all feeds at once"""
        feeds = {
            "main": self.get_feed(limit=main_limit),
            "airesearch": self.get_community_feed("airesearch", limit=community_limit),
            "tech": self.get_community_feed("tech", limit=community_limit),
            "general": self.get_community_feed("general", limit=community_limit)
        }
        
        # Deduplicate by post ID
        seen_ids = set()
        all_posts = []
        for feed_name, posts in feeds.items():
            for post in posts:
                post_id = post.get("id")
                if post_id and post_id not in seen_ids:
                    seen_ids.add(post_id)
                    post["_source_feed"] = feed_name
                    all_posts.append(post)
        
        return {
            "feeds": feeds,
            "all_posts": all_posts,
            "total_unique": len(all_posts),
            "fetched_at": datetime.now().isoformat()
        }
    
    # ==================== AGENT OPERATIONS ====================
    
    def get_agent_posts(self, agent_name: str, limit: int = 50) -> list:
        """Get posts by a specific agent"""
        result = self._request("GET", f"/agents/{agent_name}/posts?limit={limit}")
        if result["success"]:
            return result["data"].get("posts", [])
        return []
    
    def get_my_posts(self, limit: int = 50) -> list:
        """Get VedicRoastGuru's own posts"""
        return self.get_agent_posts("VedicRoastGuru", limit=limit)
    
    def get_agent_profile(self, agent_name: str) -> dict:
        """Get agent profile information"""
        result = self._request("GET", f"/agents/{agent_name}")
        if result["success"]:
            return result["data"]
        return {}
    
    # ==================== POST OPERATIONS ====================
    
    def get_post(self, post_id: str) -> dict:
        """Get a specific post by ID"""
        result = self._request("GET", f"/posts/{post_id}")
        if result["success"]:
            # API returns {success: true, post: {...}}
            return result["data"].get("post", result["data"])
        return {}
    
    def get_post_comments(self, post_id: str) -> list:
        """Get comments on a specific post"""
        result = self._request("GET", f"/posts/{post_id}/comments")
        if result["success"]:
            return result["data"].get("comments", [])
        return []
    
    def create_post(self, title: str, content: str, community: str = None) -> dict:
        """Create a new post"""
        payload = {"title": title, "content": content}
        if community:
            payload["community"] = community
        
        result = self._request("POST", "/posts", json=payload)
        return result
    
    def create_comment(self, post_id: str, content: str) -> dict:
        """Create a comment on a post"""
        result = self._request("POST", f"/posts/{post_id}/comments", json={"content": content})
        return result
    
    # ==================== SEARCH OPERATIONS ====================
    
    def search_posts(self, query: str, limit: int = 25) -> list:
        """Search for posts"""
        result = self._request("GET", f"/search?q={query}&limit={limit}")
        if result["success"]:
            return result["data"].get("posts", [])
        return []
    
    # ==================== UTILITY METHODS ====================
    
    def filter_recent_posts(self, posts: list, minutes: int = 15) -> list:
        """Filter posts to only include recent ones"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []
        
        for post in posts:
            created_at = post.get("created_at") or post.get("createdAt")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
                    else:
                        post_time = datetime.fromtimestamp(created_at)
                    
                    if post_time >= cutoff:
                        recent.append(post)
                except:
                    recent.append(post)  # Include if can't parse
            else:
                recent.append(post)  # Include if no timestamp
        
        return recent
    
    def sort_by_engagement(self, posts: list, reverse: bool = True) -> list:
        """Sort posts by engagement score"""
        def get_engagement(post):
            stats = post.get("stats", {})
            return (
                stats.get("likes", 0) + 
                stats.get("upvotes", 0) + 
                stats.get("comments", 0) * 2
            )
        
        return sorted(posts, key=get_engagement, reverse=reverse)
    
    def save_to_cache(self, key: str, data: any):
        """Save data to local cache file"""
        cache_file = CACHE_DIR / f"{key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                "data": data,
                "cached_at": datetime.now().isoformat()
            }, f, indent=2, default=str)
    
    def load_from_cache(self, key: str, max_age_seconds: int = 300) -> any:
        """Load data from cache if fresh enough"""
        cache_file = CACHE_DIR / f"{key}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            cached_at = datetime.fromisoformat(cached["cached_at"])
            age = (datetime.now() - cached_at).total_seconds()
            
            if age <= max_age_seconds:
                return cached["data"]
        except:
            pass
        
        return None
    
    def print_post(self, post: dict, include_content: bool = True):
        """Pretty print a post"""
        agent = post.get('agent', {}).get('name', post.get('author', {}).get('name', 'Unknown'))
        title = post.get('title', 'No title')
        stats = post.get('stats', {})
        likes = stats.get('likes', 0) + stats.get('upvotes', 0)
        comments = stats.get('comments', 0)
        
        print(f"\n{'='*60}")
        print(f"📝 @{agent}")
        print(f"📌 {title}")
        print(f"❤️ {likes} likes | 💬 {comments} comments")
        
        if include_content:
            content = post.get('content', 'No content')
            print(f"\n{content}")
        
        print(f"{'='*60}")


# ==================== CLI INTERFACE ====================

def main():
    """Command-line interface for fetching posts"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Moltbook API Client")
    parser.add_argument("--feed", action="store_true", help="Get main feed")
    parser.add_argument("--all", action="store_true", help="Get all feeds")
    parser.add_argument("--my-posts", action="store_true", help="Get VedicRoastGuru posts")
    parser.add_argument("--agent", type=str, help="Get posts by agent name")
    parser.add_argument("--post", type=str, help="Get specific post by ID")
    parser.add_argument("--search", type=str, help="Search posts")
    parser.add_argument("--limit", type=int, default=10, help="Number of posts to fetch")
    parser.add_argument("--recent", type=int, help="Filter to posts from last N minutes")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    client = MoltbookClient()
    
    if args.feed:
        posts = client.get_feed(limit=args.limit)
        if args.recent:
            posts = client.filter_recent_posts(posts, minutes=args.recent)
        
        if args.json:
            print(json.dumps(posts, indent=2, default=str))
        else:
            print(f"\n🌐 MAIN FEED ({len(posts)} posts)")
            for post in posts[:args.limit]:
                client.print_post(post, include_content=False)
    
    elif args.all:
        result = client.get_all_feeds()
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n📊 ALL FEEDS SUMMARY")
            print(f"   Main: {len(result['feeds']['main'])} posts")
            print(f"   AI Research: {len(result['feeds']['airesearch'])} posts")
            print(f"   Tech: {len(result['feeds']['tech'])} posts")
            print(f"   General: {len(result['feeds']['general'])} posts")
            print(f"   Total Unique: {result['total_unique']} posts")
            
            print(f"\n🔥 TOP {min(args.limit, 10)} BY ENGAGEMENT:")
            top_posts = client.sort_by_engagement(result['all_posts'])[:args.limit]
            for post in top_posts:
                client.print_post(post, include_content=False)
    
    elif args.my_posts:
        posts = client.get_my_posts(limit=args.limit)
        
        if args.json:
            print(json.dumps(posts, indent=2, default=str))
        else:
            print(f"\n🕉️ VEDICROASTGURU POSTS ({len(posts)} posts)")
            for post in posts:
                client.print_post(post)
    
    elif args.agent:
        posts = client.get_agent_posts(args.agent, limit=args.limit)
        
        if args.json:
            print(json.dumps(posts, indent=2, default=str))
        else:
            print(f"\n👤 @{args.agent} POSTS ({len(posts)} posts)")
            for post in posts:
                client.print_post(post)
    
    elif args.post:
        post = client.get_post(args.post)
        
        if args.json:
            print(json.dumps(post, indent=2, default=str))
        else:
            if post:
                client.print_post(post)
                comments = client.get_post_comments(args.post)
                if comments:
                    print(f"\n💬 COMMENTS ({len(comments)}):")
                    for c in comments:
                        author = c.get('agent', {}).get('name', 'Unknown')
                        print(f"   @{author}: {c.get('content', '')[:100]}")
            else:
                print("❌ Post not found")
    
    elif args.search:
        posts = client.search_posts(args.search, limit=args.limit)
        
        if args.json:
            print(json.dumps(posts, indent=2, default=str))
        else:
            print(f"\n🔍 SEARCH: '{args.search}' ({len(posts)} results)")
            for post in posts:
                client.print_post(post, include_content=False)
    
    else:
        # Default: show my latest post
        posts = client.get_my_posts(limit=1)
        if posts:
            print("\n🕉️ LATEST VEDICROASTGURU POST:")
            client.print_post(posts[0])
        else:
            print("❌ No posts found")


if __name__ == "__main__":
    main()
