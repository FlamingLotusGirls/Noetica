# Noetica

https://www.kickstarter.com/projects/flg/noetica-kinetic-fire-art-for-burning-man-2017

## Contributing

Use this branching model http://nvie.com/posts/a-successful-git-branching-model/

**Adding a feature**

1. Ensure you're up to date
```
git checkout develop
git pull origin develop
```
2. Branch off devleop
```
git checkout -b feature/your-thing develop
# hack, hack
git push origin feature/your-thing
```
3. Open PR with `develop` as base and `feature/your-thing` as compare
https://github.com/FlamingLotusGirls/Noetica/pulls

**Fixing a bug**

*Same as above, but prefix branch name with* `bugfix/` as in `bugfix/thing-i-fixed`
